from flask import Flask, request
import iaas

app = Flask(__name__)

@app.route("/iaas/sessions", methods="POST")
def login(): 
    creds = request.get_json()
    token = iaas.login(creds["email"], creds["password"])
    return token


# ------ Hosts
@app.route("/iaas/hosts",methods="GET")
def listHosts(): 
    token = request.headers.get("Authorization")
    query = request.args.get("query")
    hosts = iaas.listHosts(token, query)
    return hosts

@app.route("/iaas/hosts",methods="POST")
def addHost(): 
    token = request.headers.get("Authorization")
    host = request.get_json()
    host = iaas.addHost(token, host)
    return host

@app.route("/iaas/hosts/<hostID>",methods="PUT")
def updateHost(hostID): 
    token = request.headers.get("Authorization")
    host = request.get_json()
    iaas.updateHost(token,hostID,host)

@app.route("/iaas/hosts/<hostID>",methods="DELETE")
def removeHost(hostID):
    token = request.headers.get("Authorization")
    iaas.removeHost(token,hostID)


# ------ Users
@app.route("/iaas/users",methods="GET")
def listUsers(): 
    token = request.headers.get("Authorization")
    query = request.args.get("query")
    users = iaas.listUsers(token, query)
    return users

@app.route("/iaas/users",methods="POST")
def addUser(): 
    token = request.headers.get("Authorization")
    user = request.get_json()
    user = iaas.addUser(token, user)
    return user

@app.route("/iaas/users/<userID>",methods="PUT")
def updateUser(userID): 
    token = request.headers.get("Authorization")
    user = request.get_json()
    iaas.updateUser(token,userID,user)

@app.route("/iaas/users/<userID>",methods="DELETE")
def removeUser(userID):
    token = request.headers.get("Authorization")
    iaas.removeUser(token,userID)

# ------ Images
@app.route("/iaas/images",methods="GET")
def listImages(): 
    token = request.headers.get("Authorization")
    query = request.args.get("query")
    images = iaas.listImages(token, query)
    return images

@app.route("/iaas/images",methods="POST")
def addImage(): 
    token = request.headers.get("Authorization")
    img = request.get_json()
    images = iaas.addImage(token, img['url'], img)

@app.route("/iaas/images/<imageID>",methods="DELETE")
def removeImage(imageID): 
    token = request.headers.get("Authorization")
    iaas.removeImage(token, imageID)

@app.route("/iaas/images/<imageID>/shares",methods="GET")
def listImageShares(imageID): 
    token = request.headers.get("Authorization")
    imageShares = iaas.listImageShares(token, imageID)
    return imageShares

@app.route("/iaas/images/<imageID>/shares",methods="POST")
def shareImage(imageID): 
    token = request.headers.get("Authorization")
    user = request.get_json()
    iaas.shareImage(token, imageID, user['user'])

@app.route("/iaas/images/<imageID>/shares/<userID>",methods="DELETE")
def unshareImage(imageID,userID): 
    token = request.headers.get("Authorization")
    iaas.unshareImage(token, imageID,userID)

# ------ Vms

@app.route("/iaas/vms",methods="GET")
def listVms(): 
    token = request.headers.get("Authorization")
    query = request.args.get("query")
    vms = iaas.listVms(token, query)
    return vms

@app.route("/iaas/vms",methods="POST")
def addVm(): 
    token = request.headers.get("Authorization")
    vm = request.get_json()
    vm = iaas.addVm(token, vm)
    return vm

@app.route("/iaas/vms/<vmID>/start",methods="PUT")
def removeVm(vmID): 
    token = request.headers.get("Authorization")
    iaas.startVm(token,vmID)

@app.route("/iaas/vms/<vmID>/stop",methods="PUT")
def removeVm(vmID): 
    token = request.headers.get("Authorization")
    iaas.stopVm(token,vmID)

@app.route("/iaas/vms/<vmID>",methods="DELETE")
def removeVm(vmID): 
    token = request.headers.get("Authorization")
    iaas.removeVm(token,vmID)

@app.route("/iaas/vms/<vmID>/shares",methods="GET")
def listVmShares(vmID): 
    token = request.headers.get("Authorization")
    vms = iaas.listVmShares(token, vmID)
    return vms

@app.route("/iaas/vms/<vmID>/shares",methods="POST")
def shareVm(vmID): 
    token = request.headers.get("Authorization")
    user = request.get_json()
    iaas.shareVm(token, vmID, user['user'])

@app.route("/iaas/vms/<vmID>/shares/<userID>",methods="DELETE")
def unshareVm(vmID,userID): 
    token = request.headers.get("Authorization")
    iaas.unshareVm(token, vmID, userID)

@app.route("/iaas/vms/<vmID>/snapshots",methods="POST")
def saveVmAsImage(vmID): 
    token = request.headers.get("Authorization")
    vm = request.get_json()
    vm = iaas.saveVmAsImage(token, vm)
    return vm