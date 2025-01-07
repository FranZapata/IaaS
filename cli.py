import requests
import sys

def help():
    print('''
    Usage: python3 cli.py <command>
    Available commands:
        - help
        - exit
        - login <email> <password>
        - host ls [<query>]
        - host add <addr> <user> <password>
        - host rm <hostId>
        - user list [<query>]
        - user add <email> <password>
        - user rm <userId>
        - image ls [<query>]
        - image add <url> <name> <desc>
        - image rm <imgId>
        - image shares <imgId>
        - image share <imgId> <userId>
        - image unshare <imgId> <userId> 
        - vm ls [<query]
        - vm add <image> [<mem>]
        - vm start <vmId>
        - vm stop <vmId>
        - vm rm <vmId>
        - vm save <vmId> <imgName> <imgDesc>
        - vm shares <vmId>
        - vm share <vmId> <userId>
        - vm unshare <vmId> <userId> 
    ''')

token = ""

if len(sys.argv) <= 1: help()
elif sys.argv[1] == "exit": 
    pass
elif sys.argv[1] == "login": 
    creds = {"email": sys.argv[2], "password": sys.argv[3]}
    resp = requests.post("http://localhost:5000/iaas/sessions",json = creds)
    print(resp.text)
    token = resp.text
elif len(token)<1:
    print("You have to login first!!!\n")
    help()
elif sys.argv[1] == "host" and sys.argv[2] == "ls": 
    str = "http://localhost:5000/iaas/hosts"
    if len(sys.argv) == 4:
        str += f"?query={sys.argv[3]}"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "host" and sys.argv[2] == "add": 
    host = {"addr": sys.argv[3], "user": sys.argv[4], "password": sys.argv[5]}
    resp = requests.post(f"http://localhost:5000/iaas/hosts",headers={'Authorization':token}, json = host)
    print(resp)
elif sys.argv[1] == "host" and sys.argv[2] == "rm": 
    resp = requests.delete(f"http://localhost:5000/iaas/hosts/{sys.argv[3]}",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "user" and sys.argv[2] == "list": 
    str = "http://localhost:5000/iaas/users"
    if len(sys.argv) == 4:
        str += f"?query={sys.argv[3]}"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "user" and sys.argv[2] == "add": 
    user = {"email": sys.argv[3], "password": sys.argv[4]}
    resp = requests.post(f"http://localhost:5000/iaas/users",headers={'Authorization':token}, json = user)
    print(resp)
elif sys.argv[1] == "user" and sys.argv[2] == "rm": 
    resp = requests.delete(f"http://localhost:5000/iaas/hosts/{sys.argv[3]}",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "image" and sys.argv[2] == "ls": 
    str = "http://localhost:5000/iaas/images"
    if len(sys.argv) == 4:
        str += f"?query={sys.argv[3]}"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "image" and sys.argv[2] == "add": 
    img = {"url": sys.argv[3], "name": sys.argv[4], "desc": sys.argv[5]}
    resp = requests.post(f"http://localhost:5000/iaas/images",headers={'Authorization':token}, json = img)
    print(resp)
elif sys.argv[1] == "image" and sys.argv[2] == "rm": 
    resp = requests.delete(f"http://localhost:5000/iaas/images/{sys.argv[3]}",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "image" and sys.argv[2] == "shares": 
    str = f"http://localhost:5000/iaas/images/{sys.argv[3]}/shares"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "image" and sys.argv[2] == "share": 
    user = {"user": sys.argv[4]}
    resp = requests.post(f"http://localhost:5000/iaas/images/{sys.argv[3]}/shares",headers={'Authorization':token}, json = user)
    print(resp)
elif sys.argv[1] == "image" and sys.argv[2] == "unshare": 
    resp = requests.delete(f"http://localhost:5000/iaas/images/{sys.argv[3]}/shares/{sys.argv[4]}",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "vm" and sys.argv[2] == "ls": 
    str = "http://localhost:5000/iaas/vms"
    if len(sys.argv) == 4:
        str += f"?query={sys.argv[3]}"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "vm" and sys.argv[2] == "add": 
    vm = {"image": sys.argv[3]}
    if len(sys.argv)==5: vm["mem"] = sys.argv[4]
    resp = requests.post(f"http://localhost:5000/iaas/vms",headers={'Authorization':token}, json = vm)
    print(resp)
elif sys.argv[1] == "vm" and sys.argv[2] == "start": 
    resp = requests.put(f"http://localhost:5000/iaas/vms/{sys.argv[3]}/start",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "vm" and sys.argv[2] == "stop": 
    resp = requests.put(f"http://localhost:5000/iaas/vms/{sys.argv[3]}/stop",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "vm" and sys.argv[2] == "rm": 
    resp = requests.delete(f"http://localhost:5000/iaas/vms/{sys.argv[3]}",headers={'Authorization':token})
    print(resp.status_code)
elif sys.argv[1] == "vm" and sys.argv[2] == "shares": 
    str = f"http://localhost:5000/iaas/vms/{sys.argv[3]}/shares"
    resp = requests.get(str, headers={'Authorization':token})
    print(resp.json)
elif sys.argv[1] == "vm" and sys.argv[2] == "share": 
    user = {"user": sys.argv[4]}
    resp = requests.post(f"http://localhost:5000/iaas/vms/{sys.argv[3]}/shares",headers={'Authorization':token}, json = user)
    print(resp)
elif sys.argv[1] == "vm" and sys.argv[2] == "unshare": 
    resp = requests.delete(f"http://localhost:5000/iaas/vms/{sys.argv[3]}/shares/{sys.argv[4]}",headers={'Authorization':token})
    print(resp.status_code)
else: 
    help()