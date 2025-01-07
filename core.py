import sqlite3
import ansible_runner
import os
import uuid
import random
import shutil
import json
import libvirt
import traceback
from urllib.request import urlretrieve

FILE_DB = "iaas.db"
FILE_IAAS_INIT = "./plays/iaas_init.yaml"
FILE_IAAS_DESTROY = "./plays/iaas_destroy.yaml"
FILE_HOST_ADD = "./plays/host_add.yaml"
FILE_HOST_REMOVE = "./plays/host_remove.yaml"
DIR_IAAS = "/export/iaas"
DIR_IMAGES = os.path.join(DIR_IAAS,"images")
DIR_VMS = os.path.join(DIR_IAAS,"vms")
DIR_HOST_VMS = "/mnt/iaas/vms"

def init(): 
    print("init()")

    # Create DB 
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute("CREATE TABLE hosts (id varchar(32), addr varchar(32), user varchar(32), password varchar(32))")
        cur.execute("CREATE TABLE vms (id varchar(32), image varchar(32), mem varchar(32), state varchar(32), host varchar(32) FOREIGN KEY(host) REFERENCES hosts(id))") #DEFINIR FK del campo host a id de la tabla host  
        cur.execute("CREATE TABLE images (id varchar(32), name varchar(32), desc text)")

        db.commit()
    except Exception as e:
        print("Dtabase alerdy exists")
    db.close()

    # Install IaaS 
    r = ansible_runner.interface.run(
        host_pattern='localhost',
        playbook = os.path.abspath(FILE_IAAS_INIT),
        extravars={"iaas_password": "alumno"} 
    )
    if r.status == "failed": raise Exception("Ansible playbook error")


def destroy():
    print("destroy()")
    # Remove hosts
    hosts = listHosts()
    for host in hosts:
        removeHost(host['id'])

    # Uninstall IaaS
    r = r = ansible_runner.interface.run(
        host_pattern='localhost',
        playbook = os.path.abspath(FILE_IAAS_DESTROY),
        extravars={"iaas_password": "alumno"} 
    )
    if r.status == "failed": raise Exception("Ansible playbook error")

    # Destroy DB  
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute("DROP TABLE hosts")
        cur.execute("DROP TABLE vms")  
        cur.execute("DROP TABLE images")

        db.commit()
    except Exception as e:
        print("Error deleting tables")
    db.close()

def addHost(host):
    print("addHost()")

    if "addr" not in host: raise Exception("Missing host address")
    if "user" not in host: raise Exception("Missing host user")
    if "password" not in host: raise Exception("Missing host passwrod")

    hosts = listHosts(f"addr='{host['addr']}'")
    if len(hosts) > 0: raise Exception("Host already exists")

    r = ansible_runner.interface.run(
        host_pattern='target',
        inventory=f"target ansible_host={host['addr']}",
        playbook=os.path.abspath(FILE_HOST_ADD),
        extravars={
            "host_user": host['user'], 
            "host_password": host['password']} 
    )
    if r.status == "failed": raise Exception("Ansible playbook error")

    host["id"] = uuid.uuid4()

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute(f"INSERT INTO hosts VALUES('{host['id']}','{host['addr']}','{host['user']}','{host['password']}')")
    con.commit()
    con.close()
    return host



def removeHost(hostID):
    print("removeHost()")

    # Paramos vms y las eliminamos del host
    vms = listVms(f"host='{hostID}'")
    for vm in vms:
        stopVm(vm['id'])
        removeVm([vm['id']])

    # Eliminamos imagenes del host
    imgs = listImages(f"host='{hostID}'")
    for img in imgs:
        removeImage(img['id'])


    hosts = listHosts(f"id='{hostID}'")
    if len(hosts) != 1: raise Exception("Host doesn't exists or incorrect ID")

    host = hosts[0]

    r = ansible_runner.interface.run(
        host_pattern='target',
        inventory=f"target ansible_host={host['addr']}",
        playbook=os.path.abspath(FILE_HOST_REMOVE),
        extravars={
            "host_user": host['user'], 
            "host_password": host['password']} 
    )
    if r.status == "failed": raise Exception("Ansible playbook error")

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute(f"DELETE FROM hosts WHERE id like '{hostID}'")
    con.commit()
    con.close()

def updateHost(hostID, data):
        print("updateHost()")

def listHosts(query=''):
    print("listHosts")

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM hosts" + ("" if query == '' else " WHERE " + query))
    rows = cur.fetchall()
    hosts = [] 
    for row in rows:
        host = {
            "id": row[0],
            "addr": row[1],
            "user": row[2],
        } 
        hosts.append(host)
    con.close()
    return hosts

# ---------------- VMs lab2
def addVm(vm) :
    if "image" not in vm: raise Exception("Missing image")

    #  Select  hosts
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM hosts")
        rows = cur.fetchall()
        if len(rows) == 0: raise Exception("No available hosts")
        index = random.randint(0, len(rows)-1)
        host = {"id":rows[index][0],
                "addr":rows[index][1],
                "usr":rows[index][2],
        } 

        #print(json.dumps(host))

        # copy image
        src = os.path.join(DIR_IMAGES, vm["image"] + ".qcow2")
        vm["id"] = str(uuid.uuid4())
        dst = os.path.join(DIR_VMS, vm["id"] + ".qcow2")
        shutil.copyfile(src, dst)
        
        # modify permissions on file
        os.chmod(dst, 0o777)

        # configure template
        f = open("template.xml", "rt")
        template = f.read()
        f.close()

        vm["mem"] = vm["mem"] if "mem" in vm else 256000
        
        template = template.replace("{{NAME}}", vm["id"])\
            .replace("{{DISK}}", os.path.join(DIR_HOST_VMS, vm["id"] + ".qcow2"))\
            .replace("{{MEM}}", str(vm["mem"]))

        f = open(os.path.join(DIR_VMS, vm["id"] + ".xml"), "wt")
        f.write(template)
        f.close()

        # create domain
        con = libvirt.open(f"qemu+ssh://{host['usr']}@{host['addr']}/system")
        dom = con.defineXML(template)
        con.close()
        if dom == None: raise Exception("Unable to create vm")

        # save in database
        cur.execute(f"INSERT INTO vms VALUES('{vm['id']}', '{vm['image']}', {vm['mem']}, 'stopped', '{host['id']}')")
        db.commit()

    except Exception as e:
        traceback.print_exc()
        raise e

    db.close()
    return vm

def startVm(vmId): 
    print("startVM()")

    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM vms WHERE id='{vmId}'")
        rows = cur.fetchall()
        if len(rows) == 0: raise Exception("Vm not found")
        if rows[0][3] == "running": raise Exception("Vm is running")

        cur.execute(f"SELECT * FROM hosts WHERE id='{rows[0][4]}'")
        rows = cur.fetchall()
        host = {"id":rows[0][0],
                "addr":rows[0][1],
                "usr":rows[0][2],
        } 
        con = libvirt.open(f"qemu+ssh://{host['usr']}@{host['addr']}/system")
        dom = con.lookupByName(vmId)
        dom.create()
        con.close()

        cur.execute(f"UPDATE vms SET state='running' where id='{vmId}'")
        db.commit()

    except Exception as e:
        traceback.print_exc()
        raise e
    db.close()

def stopVm(vmId): 
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM vms WHERE id='{vmId}'")
        rows = cur.fetchall()
        if len(rows) == 0: raise Exception("Vm not found")
        if rows[0][3] == "stopped": raise Exception("Vm is stopped")

        cur.execute(f"SELECT * FROM hosts WHERE id='{rows[0][4]}'")
        rows = cur.fetchall()
        host = {"id":rows[0][0],
                "addr":rows[0][1],
                "usr":rows[0][2],
        } 
        con = libvirt.open(f"qemu+ssh://{host['usr']}@{host['addr']}/system")
        dom = con.lookupByName(vmId)
        dom.shutdown()
        con.close()

        cur.execute(f"UPDATE vms SET state='stopped' where id='{vmId}'")
        db.commit()

    except Exception as e:
        traceback.print_exc()
        raise e
    db.close()

def removeVm(vmId): 
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(f"SELECT * FROM vms WHERE id='{vmId}'")
        rows = cur.fetchall()
        if len(rows) == 0: raise Exception("Vm not found")

        cur.execute(f"SELECT * FROM hosts WHERE id='{rows[0][4]}'")
        rows = cur.fetchall()
        host = {"id":rows[0][0],
                "addr":rows[0][1],
                "usr":rows[0][2],
        } 
        con = libvirt.open(f"qemu+ssh://{host['usr']}@{host['addr']}/system")
        dom = con.lookupByName(vmId)
        dom.undefine()
        con.close()

        # Eliminar disco duro
        src = os.path.join(DIR_VMS, vmId + ".qcow2")
        os.remove(src)

        cur.execute(f"DELETE FROM vms WHERE id='{vmId}'")
        cur.execute(f"DELETE FROM perm WHERE resource='{vmId}' and type='vm'")
        db.commit()

    except Exception as e:
        traceback.print_exc()
        raise e
    db.close()

def listVms(query=''): 
    print("listVMs()")

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM vms" + ("" if query == '' else " WHERE " + query))
    rows = cur.fetchall()
    vms = [] 
    for row in rows:
        vm = {
            "id": row[0],
            "image": row[1],
            "mem": row[2],
            "state": row[3],
            "host": row[4],
        } 
        vms.append(vm)
    con.close()
    return vms

# ---------------------------------------------- LAB2

def addImage(url, img):
    print(f"addImage({url})")

    if "name" not in img: raise Exception("Missing name")
    if "desc" not in img: raise Exception("Missing desc")

    img["id"] = str(uuid.uuid4())
    
    # copy file
    urlretrieve(url, os.path.join(DIR_IMAGES,img["id"] + ".qcow2"))

    #  insert into db
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(F"INSERT INTO images VALUES('{img['id']}', '{img['name']}', '{img['desc']}')")
        db.commit()
    except Exception as e:
        traceback.print_exc()
        raise e

    db.close()
    return img

def saveVmAsImage(vmId,img): 
    print(f"saveVmAsImage({vmId})")

    if "name" not in img: raise Exception("Missing name")
    if "desc" not in img: raise Exception("Missing desc")

    # Paramos la vm
    stopVm(vmId)

    img["id"] = str(uuid.uuid4())

    # copy file
    src = os.path.join(DIR_VMS, vmId + ".qcow2")
    dst = os.path.join(DIR_IMAGES, img["id"] + ".qcow2")
    shutil.copyfile(src, dst)

    #  insert into db
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        cur.execute(F"INSERT INTO images VALUES('{img['id']}', '{img['name']}', '{img['desc']}')")
        db.commit()
    except Exception as e:
        traceback.print_exc()
        raise e

    db.close()
    return img
    

def removeImage(imgId):
    db = sqlite3.connect(FILE_DB)
    cur = db.cursor()
    try:
        # Eliminar imagen
        src = os.path.join(DIR_IMAGES, imgId + ".qcow2")
        os.remove(src)

        cur.execute(f"DELETE FROM images WHERE id='{imgId}'")
        cur.execute(f"DELETE FROM perm WHERE resource='{imgId}' and type='image'")
        db.commit()

    except Exception as e:
        traceback.print_exc()
        raise e
    db.close()

def listImages(query=""):
    print("listImages()")

    con = sqlite3.connect(FILE_DB)
    cur = con.cursor()
    cur.execute("SELECT * FROM images" + ("" if query == '' else " WHERE " + query))
    rows = cur.fetchall()
    images = [] 
    for row in rows:
        img = {
            "id": row[0],
            "name": row[1],
            "desc": row[2],
        } 
        images.append(img)
    con.close()
    return images