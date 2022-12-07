import sys
from socket import *
import datetime
import uuid
import Pyro4
import constants
import re
from cryptography.fernet import Fernet
import crypto
import random

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

def callPeerForList(peer, clientRequest):
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        return serverResponse.split("|")[1]
    else:
        print(serverResponse.split("|")[1])
        return ""

def callPeerForRead(peer, clientRequest, encKey):
    # decryptedFileText = crypto.fernetDecryption(serverResponse.split("|")[1],encKey)
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print("\n----------------------------------------")
        print("File Content:\n")
        print(crypto.fernetDecryption(serverResponse.split("|")[1],encKey))
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
    if indexServerResponse.split("|")[0] == "1":
        print(indexServerResponse.split("|")[1])
        return True
    else:
        print(indexServerResponse.split("|")[1])
        return False


def createFileOrDirectory(fileName, permissions, userId, path, directoryFlag):
    i = 0
    userList = ""
    createMsg = """
    Enter
    1 -> Create Locally
    2 -> Create Everywhere
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
        encKey = str(Fernet.generate_key().decode())
        encKey = encKey.lstrip("b'")
        encKey = encKey.rstrip("'")
        encKey = encKey + "|||" + str(random.randrange(1,26,4))
        fileIndexServer.storeEncryptionKey(str(hash(fileName)),encKey)
        encryptedFileName = crypto.fileNameEncryption(fileName.split(".")[1], encKey.split("|||")[1])

        if directoryFlag:
            encryptedFileName = path+encryptedFileName
        else:
            encryptedFileName = path+encryptedFileName+".txt"

        clientRequest = "CREATE_FILE"+"|"+userId+"|"+encryptedFileName+"|"+str(hash(fileName))+"|"+permissions+"|"+userList.strip("\n")+"|"+str(datetime.datetime.now())
        while True:
            print(createMsg)
            opt = int(input())
            if opt == 1 or opt == 2:
                break
            else:
                print("Invalid option selected")

        
        if opt == 2:
            peer = fileIndexServer.getAllPeers()
            if peer.split("|")[0] == "0":
                print("\n----------------------------------------")
                print("Unable to find peers in the network. File can be created only locally")
                print("\n----------------------------------------")
            else:
                callPeer(peer, clientRequest)
        else:
            callPeer(constants.peerName+","+constants.pyroHost, clientRequest)



def writeFile(fileName, userId, path):
    
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
    peer = fileIndexServer.getPeerUriForRead(str(hash(fileName)))
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        peerName,nsIP = peer.split(",")
        nsIP = nsIP.strip("\n")
        nameserver=Pyro4.locateNS(host = nsIP)
        peerUri = nameserver.lookup(peerName)
        peerObj = Pyro4.Proxy(peerUri)
        response = peerObj.verifyFilePermission(userId, str(hash(fileName)))
        if response.split("|")[0] == "0":
            print("Access denied")
        else:
            encKey = fileIndexServer.getEncryptionKey(str(hash(fileName)))
            # encKey = encKey.lstrip("b'")
            # encKey = encKey.rstrip("'")
            encryptedFileName = crypto.fileNameEncryption(fileName.split(".")[1], encKey.split("|||")[1])
            print(encryptedFileName)
            encryptedFileName = path+encryptedFileName+".txt"

            encryptedFileText = crypto.fernetEncryption(fileText,encKey.split("|||")[0])
            clientRequest = "WRITE_FILE"+"|"+userId+"|"+encryptedFileName+"|"+encryptedFileText+"|"+str(hash(fileText))+"|"+ curr_time
            peer = fileIndexServer.lockAndGetPeerURI(str(hash(fileName)))
            if peer.split("|")[0] == "0":
                print(peer.split("|")[1])
            else:
                for i,peer in enumerate(peer.split("|")):
                    if i !=0:
                        callPeer(peer, clientRequest)
            fileIndexServer.unlockFileWrite(str(hash(fileName)), str(hash(fileText)), curr_time)    


def readFile(fileName, userId, path):
    peer = fileIndexServer.getPeerUriForRead(str(hash(fileName)))
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        peerName,nsIP = peer.split(",")
        nsIP = nsIP.strip("\n")
        nameserver=Pyro4.locateNS(host = nsIP)
        peerUri = nameserver.lookup(peerName)
        peerObj = Pyro4.Proxy(peerUri)
        response = peerObj.verifyFilePermission(userId, str(hash(fileName)))
        if response.split("|")[0] == "0":
            print("Access denied")
        else:
            encKey = fileIndexServer.getEncryptionKey(str(hash(fileName)))
            # encKey = encKey.lstrip("b'")
            # encKey = encKey.rstrip("'")
            encKey = encKey + "|||" + str(random.randrange(10,26,4))
            encryptedFileName = crypto.fileNameEncryption(fileName.split(".")[1], encKey.split("|||")[1])
            encryptedFileName = path+encryptedFileName+".txt"
            clientRequest = "READ_FILE"+"|"+userId+"|"+encryptedFileName + "|" + str(hash(fileName))
            callPeerForRead(peer, clientRequest, encKey.split("|||")[0])


def deleteFile(fileName, userId):
    clientRequest = "DELETE_FILE"+"|"+userId+"|"+str(hash(fileName))

    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(str(hash(fileName)))

    if callPeer(peer,clientRequest):
        msg = fileIndexServer.performFileDelete(str(hash(fileName)))
    
    print(msg.split("|")[1])
    

def restoreFile(fileName, userId):
    clientRequest = "RESTORE_FILE"+"|"+userId+"|"+str(hash(fileName))

    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(str(hash(fileName)))
    if callPeer(peer,clientRequest):
        msg = fileIndexServer.performFileRestore(str(hash(fileName)))
    
    print(msg.split("|")[1])



def goInsideDirectory(directoryname):
    if not verifyFileAvailability(str(hash(directoryname))):
        return True
    else:
        return False


def listFilesInCurrentPath(userId,path):
    peerList = fileIndexServer.getAllPeers()
    updatedPath =path
    if not path == "./db":
        updatedPath = "."
        traversedPath = "/"
        for i, dir in enumerate(path.strip(".").split("/")):
            if not dir == "":
                if dir == "db":
                    updatedPath = updatedPath + "/db"
                    traversedPath = traversedPath + "db/"
                else:
                    encKey = fileIndexServer.getEncryptionKey(str(hash(path.split(dir)[0] + dir))).split("|||")[1]
                    updatedPath =  updatedPath + "/" +crypto.fileNameEncryption(traversedPath + dir,encKey)
                    traversedPath = traversedPath + dir
                    print(updatedPath)

    clientRequest = "LIST_FILES|"+userId+"|"+updatedPath
    fileList = []
    fileList = fileList + callPeerForList(peerList.split("|")[0],clientRequest).split(",")
    print("--------------------------------------")
    if not len(fileList) == 0:
        print("Files available in current directory:")
        for i, file in enumerate(fileList):
            if not file == "":
                fileName,fileNameHash = file.split(" ")
                encKey = fileIndexServer.getEncryptionKey(fileNameHash).split("|||")[1]
                decFileName = crypto.fileNameDecryption(fileName.split(".")[0],encKey)
                decFileName = decFileName + ".txt" if ".txt" in fileName else decFileName
                print(decFileName.strip(path.lstrip(".")))
        





