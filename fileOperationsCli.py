import sys
from socket import *
import datetime
import uuid
import Pyro4
import constants

# fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
localPeer = Pyro4.Proxy("PYRONAME:"+constants.peerName)


def callPeerCopy(nsIP, peer,clientRequest):
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peer)
    peer = Pyro4.Proxy(peerUri)
    serverResponse = peer.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print("\n----------------------------------------")
        print("Server response:\n")
        print(serverResponse.split("|")[1])
        print("----------------------------------------")
        return True
    else:
        print(serverResponse.split("|")[1])
        return False


def callPeer(peer, clientRequest):
    #Client creating api request to server
    peerObj = Pyro4.Proxy("PYRONAME:"+peer)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print("\n----------------------------------------")
        print("Server response:\n")
        print(serverResponse.split("|")[1])
        print("----------------------------------------")
        return True
    else:
        print(serverResponse.split("|")[1])
        return False

def verifyFileAvailability(fileNameHash):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    jsonObject = {
        "fileNameHash": fileNameHash
    }
    indexServerResponse = fileIndexServer.checkFileAvailability(jsonObject)
    print(indexServerResponse)
    if indexServerResponse.split("|")[0] == "1":
        print(indexServerResponse.split("|")[1])
        return True
    else:
        print(indexServerResponse.split("|")[1])
        return False

def createFile(fileName, permissions, userId):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    i = 0
    userList = ""
    createMsg = """
    Enter
    1 -> Create Locally
    2 -> Create Locally and a Peer
    """
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
                print("\n----------------------------------------")
                print("Unable to find peers in the network. File can be created only locally")
                print("\n----------------------------------------")
            else:
                callPeer(peer, clientRequest)
        return callPeer(constants.peerName, clientRequest)
        


        



def writeFile(fileName, userId):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
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
        for i,peer in enumerate(peer.split("|")):
            if i !=0:
                callPeer(peer, clientRequest)
    fileIndexServer.unlockFileWrite(str(hash(fileName)), str(hash(fileText)), curr_time)


def readFile(fileName, userId):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    clientRequest = "READ_FILE"+"|"+userId+"|"+fileName
    peer = fileIndexServer.getPeerUriForRead(str(hash(fileName)))
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        callPeer(peer, clientRequest)

def deleteFile(fileName, userId):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)

    clientRequest = "DELETE_FILE"+"|"+userId+"|"+fileName

    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(str(hash(fileName)))

    if callPeer(peer,clientRequest):
        msg = fileIndexServer.performFileDelete(str(hash(fileName)))
    
    print(msg.split("|")[1])
    

def restoreFile(fileName, userId):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    clientRequest = "RESTORE_FILE"+"|"+userId+"|"+fileName

    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(str(hash(fileName)))
    if callPeer(peer,clientRequest):
        msg = fileIndexServer.performFileRestore(str(hash(fileName)))
    
    print(msg.split("|")[1])



def goInsideDirectory(directoryname):
    if verifyFileAvailability(str(hash(directoryname))):
        return True
    else:
        return False

def listFilesInCurrentPath(userId,path):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    peerList = fileIndexServer.getAllPeers()
    clientRequest = "LIST_FILES|"+userId+path
    for i, uri in enumerate(peerList):
        callPeer(uri,clientRequest)



