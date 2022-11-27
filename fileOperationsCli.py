import sys
from socket import *
import datetime
import uuid
import Pyro4
import constants

fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
localPeer = Pyro4.Proxy("PYRONAME:"+constants.peerName)

def callFileIndexServer(indexServerRequest):
    indexServerResponse = fileIndexServer.checkFileAvailability(indexServerRequest)
    if indexServerResponse.split("|")[0] == "1":
        print(indexServerResponse.split("|")[1])
        return True
    else:
        print(indexServerResponse.split("|")[1])
        return False


def callPeer(peer, clientRequest):
    #Client creating api request to server
    peerObj = Pyro4.Proxy("PYRONAME:"+peer)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print(serverResponse.split("|")[1])
        return True
    else:
        print(serverResponse.split("|")[1])
        return False

def verifyFileAvailability(fileNameHash):
    indexServerResponse = fileIndexServer.checkFileAvailability(fileNameHash)
    if indexServerResponse.split("|")[0] == "1":
        print(indexServerResponse.split("|")[1])
        return True
    else:
        print(indexServerResponse.split("|")[1])
        return False

def createFile(fileName, permissions, userId):
    i = 0
    userList = ""
    createMsg = """
    Enter
    1 -> Create Locally
    2 -> Create Locally and a Peer
    """
    print(createMsg)
    opt = int(input())

    if verifyFileAvailability(str(hash(fileName))):
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

        clientRequest = "CREATE_FILE"+"|"+userId+"|"+fileName+"|"+permissions+"|"+userList.strip("\n")+"|"+str(datetime.datetime.now())
        
        while True:
            print(createMsg)
            opt = int(input())
            if opt == 1 or opt == 2:
                break
            else:
                print("Invalid option selected")

        
        if opt == 2:
            peer = fileIndexServer.getAvailablePeerURI(constants.peerName)
            if peer.split("|")[0] == "0":
                print(peer.split("|")[1])
            else:
                callPeer(peer, clientRequest)
        return callPeer(constants.peerName, clientRequest)
        


        



def writeFile(fileName, userId):

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

    curr_time = str(datetime.datetime.now())
    clientRequest = "WRITE_FILE"+"|"+userId+"|"+fileName+"|"+fileText+"|"+str(hash(fileText))+"|"+ curr_time
    peer = fileIndexServer.lockAndGetPeerURI(str(hash(fileName)))
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        for i,peer in enumerate(peer.strip("|")):
            if i !=0:
                callPeer(peer, clientRequest)
    fileIndexServer.unlockFileWrite(str(hash(fileName)), str(hash(fileText)), curr_time)


def readFile(fileName, userId):
    clientRequest = "READ_FILE"+"|"+userId+"|"+fileName
    peer = fileIndexServer.getPeerUriForRead(str(hash(fileName)))
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        callPeer(peer, clientRequest)

def deleteFile(fileName, userId):

    deleteMsg = """
    Enter
    1 -> Delete locally
    2 -> Delete everywhere
    Note: If you delete everywhere you won't be able to restore the file
    """
    print(deleteMsg)

    while True:
        print(deleteMsg)
        opt = int(input())
        if opt == 1 or opt == 2:
            break
        else:
            print("Invalid option selected")


    clientRequest = "DELETE_FILE"+"|"+userId+"|"+fileName
    peer = fileIndexServer.getPeerURIForDelete(str(hash(fileName)))
    if opt == 2:
        for i,peer in enumerate(peer.strip("|")):
            if i !=0:
                callPeer(peer, clientRequest)
    else:
        return callPeer(constants.peerName, clientRequest)
