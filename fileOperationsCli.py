import sys
from socket import *
import datetime
import uuid
import Pyro4
import constants
import re


fileNamePattern = re.compile("^([A-Za-z0-9])+(.txt)?$")
# fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
# localPeer = Pyro4.Proxy("PYRONAME:"+constants.peerName)

nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
fileIndexUri = nameserver.lookup("example.fileIndex")
fileIndexServer = Pyro4.Proxy(fileIndexUri)

def callPeer(peer,clientRequest):
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
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
    i = 0
    userList = ""
    createMsg = """
    Enter
    1 -> Create Locally
    2 -> Create Locally and a Peer
    """
    print(fileName)
    if verifyFileAvailability(str(hash(fileName))):
        
        if "p" not in permissions and re.fullmatch(fileNamePattern, fileName):
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
        return callPeer(constants.peerName+","+constants.pyroHost, clientRequest)



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
        for i,peer in enumerate(peer.split("|")):
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
    clientRequest = "DELETE_FILE"+"|"+userId+"|"+fileName

    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(str(hash(fileName)))

    if callPeer(peer,clientRequest):
        msg = fileIndexServer.performFileDelete(str(hash(fileName)))
    
    print(msg.split("|")[1])
    

def restoreFile(fileName, userId):
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
    peerList = fileIndexServer.getAllPeers()
    clientRequest = "LIST_FILES|"+userId+"|"+path
    for i, peer in enumerate(peerList.split("|")):
        callPeer(peer,clientRequest)



