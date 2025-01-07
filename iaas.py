from wsgiref import validate
import core
import sqlite3
import traceback
import time
import cryptocode
import json
import uuid

FILE_DB = "iaas.db"
PASSWORD = "password"

def init():
    core.init()

    # Create DB 
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute("CREATE TABLE users (id varchar(32), email varchar(32) UNIQUE, password varchar(32), quota text, admin int)")
        cur.execute("INSERT INTO users VALUES('0', 'root', 'root', '{}', 1)")
        cur.execute("CREATE TABLE perms (user varchar(32), resource varchar(32), type varchar(32))")
        db.commit()
    except Exception as e:
        print("Dtabase alerdy exists")
    db.close()

# Gestion de usuarios ----------------------------

def login(email, password) :
    print(f"login({email}, {password})")

    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM users WHERE email='{email}' and password='{password}'")
        rows = cur.fetchall()
        if len(rows) == 0: raise Exception("Wrong authentication")
        data = {
            "user": {
                "id": rows[0][0],
                "email": rows[0][1],
                "admin": rows[0][4]
            },
            "ts": time.time_ns()
        }
        token = cryptocode.encrypt(json.dumps(data),PASSWORD)
        return token
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()


def validateToken(token) :
    print(f"validateToken({token})")

    data = cryptocode.decrypt(token, PASSWORD)
    if not data: raise Exception("Invalid token")

    data = json.loads(data)
    
    # Comprobar que data["ts"] no está caducado

    return data["user"]


def addUser(token, user) :
    print(f"addUser()")

    issuer = validateToken(token)

    if not issuer["admin"]: raise Exception("Unauthorized")

    if "email" not in user: raise Exception("Missing email")
    if "password" not in user: raise Exception("Missing password")

    if "admin" not in user: user["admin"] = 0
    if "quota" not in user: user["quota"] = "{}"

    user["id"] = str(uuid.uuid4())

    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"INSERT INTO users VALUES('{user['id']}','{user['email']}','{user['password']}', '{user['quota']}', {user['admin']})")
        del user["password"]
        return user
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()

    


def removeUser(token,userId):
    issuer = validateToken(token)

    if not issuer["admin"]: raise Exception("Unauthorized")

    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"DELETE FROM users WHERE id like '{userId}'")
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()


def updateUser(token, userId,data):
    issuer = validateToken(token)

    if not issuer["admin"] and issuer["id"] != userId: raise Exception("Unauthorized")

    query = "UPDATE user SET "

    for field in data:
        query += f"{field} = '{data[field]}', "
    query = query[:-2]

    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(query)
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()


def listUsers(token, query=""):
    try:
        validateToken(token)
    except Exception as e:
        traceback.print_exc()
        raise e

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM users" + ("" if query == '' else " WHERE " + query))
    rows = cur.fetchall()
    users = [] 
    for row in rows:
        user = {
            "id": row[0],
            "email": row[1],
            "quota": json.loads(row[3]),
            "admin": row[4],
        } 
        users.append(user)
    con.close()
    return users


# Control de accesos HOSTS -----------------------------

def addHost(token, host):
    issuer = validateToken(token)
    if not issuer["admin"]: raise Exception("Unauthorized")
    host = core.addHost(host)
    return host


def listHosts(token, query="") :
    issuer = validateToken(token)
    return core.listHosts(query)


def updateHost(token,hostId,data):
    issuer = validateToken(token)
    if not issuer["admin"]: raise Exception("Unauthorized")
    host = core.updateHost(hostId,data)
    return host


def removeHost(token,hostId):
    issuer = validateToken(token)
    if not issuer["admin"]: raise Exception("Unauthorized")
    host = core.removeHost(hostId)
    return host


# Control de accesos IMAGES -----------------------------

def addImage(token, url,img):
    issuer = validateToken(token)
    img = core.addImage(url, img)
    
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"INSERT INTO perms VALUES('{issuer['id']}','{img['id']}','image')")
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()  

    return img  


def listImages(token,query=""):
    issuer = validateToken(token)

    if issuer["admin"]:
        images = core.listImages(query)
        return images
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and type='image'")
            rows = cur.fetchall()
            ids = [f"{row[1]}" for row in rows]
            if len(query): query += " AND id in ('" + "','".join(ids) + "')"
            else: query = "id in ('" + "','".join(ids) + "')"
            images = core.listImages(query)
            return images
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close() 


def removeImage(token,imgId):
    issuer = validateToken(token)

    if issuer["admin"]:
        images = core.removeImage(imgId)
        return images
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{imgId}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                core.removeImage(imgId)
                return "Image removed."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close()


# Control de accesos VMs -----------------------------

def addVm(token, vm):
    issuer = validateToken(token)

    if issuer["admin"]:
        vm = core.addVm(vm)
        return vm
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vm['image']}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                vm = core.addVm(vm)
                cur.execute(f"INSERT INTO perms VALUES ('{issuer['id']}','{vm['id']}','vm')")
                return "Vm added."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close()


def listVms(token, query=""):
    issuer = validateToken(token)

    if issuer["admin"]:
        vms = core.listVms(query)
        return vms
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and type='vm'")
            rows = cur.fetchall()
            ids = [f"{row[1]}" for row in rows]
            if len(query): query += " AND id in ('" + "','".join(ids) + "')"
            else: query = "id in ('" + "','".join(ids) + "')"
            vms = core.listVms(query)
            return vms


        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close() 


def startVm(token, vmId):
    issuer = validateToken(token)

    if issuer["admin"]:
        core.startVm(vmId)
        return "Vm added."
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                core.startVm(vmId)
                return "Vm added."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close()

def stopVm(token, vmId):
    issuer = validateToken(token)

    if issuer["admin"]:
        core.stopVm(vmId)
        return "Vm stopped"
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                core.stopVm(vmId)
                return "Vm stopped."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close() 

def removeVm(token, vmId):
    issuer = validateToken(token)

    if issuer["admin"]:
        core.removeVm(vmId)
        return "Vm stopped"
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                core.removeVm(vmId)
                return "Vm removed."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close()            

def saveVmAsImage(token, vm):
    issuer = validateToken(token)

    if issuer["admin"]:
        vm = core.saveVmAsImage(vm)
        return vm
    else:
        db = sqlite3.connect(FILE_DB)
        cur = db.cursor()
        try:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vm['image']}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                vm = core.saveVmAsImage(vm)
                cur.execute(f"INSERT INTO perms VALUES ('{issuer['id']}','{vm['id']}','vm')")
                return "Vm added."
        except Exception as e:
            traceback.print_exc()
            raise e
        finally:
            db.commit()
            db.close()

# Comparticion de recursos Vms ---------------------------

def shareVm(token, vmId,userId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"INSERT INTO perms VALUES ('{userId}','{vmId}','vm')")
            return "Vm shared."
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"INSERT INTO perms VALUES ('{userId}','{vmId}','vm')")
                return "Vm shared."
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close() 

def unshareVm(token, vmId,userId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"DELETE FROM perms WHERE user='{userId}' and resource='{vmId}' and type='vm')")
            return "Vm unshared."
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"DELETE FROM perms WHERE user='{userId}' and resource='{vmId}' and type='vm')")
                return "Vm unshared."
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()

def listVmShares(token, vmId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"SELECT FROM perms WHERE resource='{vmId}' and type='vm')")
            rows = cur.fetchall()
            perms = [] 
            for row in rows:
                perm = {
                    "user": row[0],
                    "resource": row[1],
                    "type": row[2]
                } 
                perms.append(perm)
            return perms
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{vmId}' and type='vm'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"SELECT FROM perms WHERE resource='{vmId}' and type='vm')")
                rows = cur.fetchall()
                perms = [] 
                for row in rows:
                    perm = {
                        "user": row[0],
                        "resource": row[1],
                        "type": row[2]
                    } 
                    perms.append(perm)
                return perms
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close() 


# Comparticion de recursos Images ---------------------------

def shareImage(token,imgId,userId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"INSERT INTO perms VALUES ('{userId}','{imgId}','image')")
            return "VImage shared."
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{imgId}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"INSERT INTO perms VALUES ('{userId}','{imgId}','image')")
                return "Image shared."
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close() 

def unshareImage(token,imgId,userId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"DELETE FROM perms WHERE user='{userId}' and resource='{imgId}' and type='image')")
            return "Image unshared."
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{imgId}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"DELETE FROM perms WHERE user='{userId}' and resource='{imgId}' and type='image')")
                return "Image unshared."
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close()

def listImageShares(token, imgId):
    issuer = validateToken(token)
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        if issuer["admin"]:
            cur.execute(f"SELECT FROM perms WHERE resource='{imgId}' and type='image')")
            rows = cur.fetchall()
            perms = [] 
            for row in rows:
                perm = {
                    "user": row[0],
                    "resource": row[1],
                    "type": row[2]
                } 
                perms.append(perm)
            return perms
        else:
            cur.execute(f"SELECT * FROM perms WHERE user='{issuer['id']}' and resource = '{imgId}' and type='image'")
            rows = cur.fetchall()
            if len(rows)>0:
                cur.execute(f"SELECT FROM perms WHERE resource='{imgId}' and type='image')")
                rows = cur.fetchall()
                perms = [] 
                for row in rows:
                    perm = {
                        "user": row[0],
                        "resource": row[1],
                        "type": row[2]
                    } 
                    perms.append(perm)
                return perms
    except Exception as e:
        traceback.print_exc()
        raise e
    finally:
        db.commit()
        db.close() 


# ---------------- Gestion cuotas usuarios
def checkQuota():
    pass