import sys
from socket import *

dbAddress = "localhost"
dbPort = 9000


def socketConnection():
    #AF_INET represents which family address type belongs to.
    sock = socket(AF_INET, SOCK_STREAM)
    return sock

def callPeer(peer, clientRequest):
    #Client creating api request to server
    serverResponse = peer.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print(serverResponse.split("|")[1])
        return True
    else:
        print(serverResponse.split("|")[1])
        return False




def createFile(peer, fileName, path, permissions, userId):
    i = 0
    userList = ""
    if "p" not in permissions:
        print("Please enter userlist who has access to this file\n")
        print("Note: After finishing enter [end]")
        print("-------------------------------------------------------\n")

        while True:
            inp = sys.stdin.readline()
            inp = inp.strip('\n')
            if "[end]" in inp:
                break
            else:
                if i == 0:
                    userList += inp
                else:
                    userList += "," + inp
            i += 1
        print("-------------------------------------------------------\n")

    clientRequest = "CREATE_FILE"+"|"+userId+"|"+fileName+"|"+path+"|"+permissions+"|"+userList

    return callPeer(peer, clientRequest)



def writeFile(peer, fileName, path, userId):
    fileText = ""
    print("Please enter file content\n")
    print("Note: After finishing enter [end] in new line")
    print("-------------------------------------------------------\n")

    while True:
        inp = sys.stdin.readline()
        if "[end]" in inp:
                break
        else:
            fileText+=inp

    print("-------------------------------------------------------\n")

    clientRequest = "WRITE_FILE"+"|"+userId+"|"+fileName+"|"+path+"|"+fileText
    return callPeer(peer, clientRequest)


def readFile(peer, fileName, path, userId):
    clientRequest = "READ_FILE"+"|"+userId+"|"+fileName+"|"+path
    return callPeer(peer, clientRequest)

def deleteFile(peer, fileName, path, userId):
    clientRequest = "DELETE_FILE"+"|"+userId+"|"+fileName+"|"+path
    return callPeer(peer, clientRequest)
