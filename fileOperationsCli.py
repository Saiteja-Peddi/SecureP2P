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
import hashlib

fileNamePattern = re.compile("^([A-Za-z0-9])+(.txt)?$")
directoryNamePattern = re.compile("^([A-Za-z0-9])+$")
# fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
# localPeer = Pyro4.Proxy("PYRONAME:"+constants.peerName)

nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
fileIndexUri = nameserver.lookup("example.fileIndex")
fileIndexServer = Pyro4.Proxy(fileIndexUri)




def createHash(fileName):
    hash = str(hashlib.shake_128("saiteja".encode()).digest(30))
    return hash

def callPeer(peer,clientRequest, printResponse = True):
    clientRequest = crypto.fernetEncryption(clientRequest, constants.peerCommEncKey)
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    serverResponse = crypto.fernetDecryption(serverResponse, constants.peerCommEncKey)
    if printResponse:
        print("\n----------------------------------------")
        print("Server response:\n")
        print(serverResponse.split("|")[1])
        print("----------------------------------------")
    if serverResponse.split("|")[0] == "1":
        return True
    else:
        return False

def callPeerForList(peer, clientRequest):
    clientRequest = crypto.fernetEncryption(clientRequest, constants.peerCommEncKey)
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    serverResponse = crypto.fernetDecryption(serverResponse, constants.peerCommEncKey)
    if serverResponse.split("|")[0] == "1":
        return serverResponse.split("|")[1]
    else:
        print(serverResponse.split("|")[1])
        return ""

def callPeerForRead(peer, clientRequest, encKey):
    print(encKey)
    clientRequest = crypto.fernetEncryption(clientRequest, constants.peerCommEncKey)
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    serverResponse = crypto.fernetDecryption(serverResponse, constants.peerCommEncKey)
    if serverResponse.split("|")[0] == "1":
        print("\n----------------------------------------")
        print("File Content:\n")
        print(crypto.fernetDecryption(serverResponse.split("|")[1],encKey))
        print("----------------------------------------")
        return True
    else:
        print(serverResponse.split("|")[1])
        return False

def verifyFileAvailability(fileNameHash, pathChange = False):
    indexServerResponse = fileIndexServer.checkFileAvailability(fileNameHash)
    indexServerResponse = crypto.fernetDecryption(indexServerResponse, constants.peerCommEncKey)
    if not pathChange:
        print(indexServerResponse.split("|")[1])
    if indexServerResponse.split("|")[0] == "1":
        return True
    else:
        return False


def verifyFileAvailabilityForCreate(fileName):
    peer = fileIndexServer.getAllPeers()
    peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
    fileAvailableCount = 0
    clientRequest = "FILE_AVAILABLE|"+fileName
    if peer.split("|")[0] == "0":
        print("\n----------------------------------------")
        print("Unable to find peers in the network. File can be created only locally")
        print("\n----------------------------------------")
    else:
        for i,peerURI in enumerate(peer.split("|")):
            response = callPeer(peerURI, clientRequest, False)
            print(response)
            if response:
                fileAvailableCount = fileAvailableCount + 1
    print(len(peer.split("|")))
    print(fileAvailableCount)
    if fileAvailableCount == len(peer.split("|")):
        return True
    else:
        print("File already exist")
        


def verifyFileLock(fileNameHash):
    response = fileIndexServer.checkFileLock(fileNameHash)
    response = crypto.fernetDecryption(response, constants.peerCommEncKey)
    if response.split("|")[0] == 0:
        print(response.split("|")[1])
        return False
    else:
        return True


def createFileOrDirectory(fileName, permissions, userId, path, directoryFlag):
    i = 0
    userList = ""
    createMsg = """
    Enter
    1 -> Create Locally
    2 -> Create Everywhere
    """
    if verifyFileAvailabilityForCreate(createHash(fileName)):
        
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
        storeEncReq = crypto.fernetEncryption(createHash(fileName)+" "+encKey, constants.fileIndexEncKey)
        fileIndexServer.storeEncryptionKey(storeEncReq)
        encryptedFileName = crypto.fileNameEncryption(fileName.split("/")[-1].rstrip(".txt"), encKey.split("|||")[1])

        if directoryFlag:
            encryptedFileName = getEncryptPath(path)+encryptedFileName
        else:
            encryptedFileName = getEncryptPath(path)+encryptedFileName+".txt"
        print(fileName)
        fileText = "Please enter file content"
        fileText = crypto.fernetEncryption(fileText, encKey.split("|||")[0])
        clientRequest = "CREATE_FILE"+"|"+userId+"|"+encryptedFileName+"|"+createHash(fileName)+"|"+ fileText +"|"+permissions+"|"+userList.strip("\n")+"|"+str(datetime.datetime.now())
        while True:
            print(createMsg)
            opt = int(input())
            if opt == 1 or opt == 2:
                break
            else:
                print("Invalid option selected")

        
        if opt == 2:
            peer = fileIndexServer.getAllPeers()
            peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
            if peer.split("|")[0] == "0":
                print("\n----------------------------------------")
                print("Unable to find peers in the network. File can be created only locally")
                print("\n----------------------------------------")
            else:
                for i,peer in enumerate(peer.split("|")):
                    callPeer(peer, clientRequest)
        else:
            callPeer(constants.peerName+","+constants.pyroHost, clientRequest)



def writeFile(fileName, userId, path):
    if verifyFileLock(createHash(fileName)):
        peer = fileIndexServer.getPeerUriForRead(createHash(fileName))
        peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
        if peer.split("|")[0] == "0":
            print(peer.split("|")[1])
        else:
            permissionReq = "VERIFY_PERMISSION|"+userId+"|"+createHash(fileName)+"|"+"w"
            response = callPeer(peer, permissionReq)
            # response = peerObj.verifyFilePermission(userId, createHash(fileName))
            if response:
                peer = fileIndexServer.lockAndGetPeerURI(createHash(fileName))
                peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
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
                encKey = fileIndexServer.getEncryptionKey(createHash(fileName))
                encKey = crypto.fernetDecryption(encKey, constants.peerCommEncKey)
                encryptedFileName = crypto.fileNameEncryption(fileName.split("/")[-1].rstrip(".txt"), encKey.split("|||")[1])
                encryptedFileName = getEncryptPath(path)+encryptedFileName+".txt"
                encryptedFileText = crypto.fernetEncryption(fileText,encKey.split("|||")[0])
                clientRequest = "WRITE_FILE"+"|"+userId+"|"+encryptedFileName+"|"+encryptedFileText+"|"+createHash(fileText)+"|"+ curr_time
                
                if peer.split("|")[0] == "0":
                    print(peer.split("|")[1])
                else:
                    print(peer)
                    for i,peer in enumerate(peer.split("|")):
                        callPeer(peer, clientRequest)
                indexServReq = createHash(fileName) +"$"+ createHash(fileText) +"$"+ curr_time
                indexServReq = crypto.fernetEncryption(indexServReq, constants.fileIndexEncKey)
                fileIndexServer.unlockFileWrite(indexServReq)    


def readFile(fileName, userId, path):
    if verifyFileLock(createHash(fileName)):
        peer = fileIndexServer.getPeerUriForRead(createHash(fileName))
        peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
        if peer.split("|")[0] == "0":
            print(peer.split("|")[1])
        else:
            permissionReq = "VERIFY_PERMISSION|"+userId+"|"+createHash(fileName)+"|"+"r"
            response = callPeer(peer, permissionReq)
            # response = peerObj.verifyFilePermission(userId, createHash(fileName))
            if response:
                encKey = fileIndexServer.getEncryptionKey(createHash(fileName))
                encKey = crypto.fernetDecryption(encKey, constants.peerCommEncKey)
                encryptedFileName = crypto.fileNameEncryption(fileName.split("/")[-1].rstrip(".txt"), encKey.split("|||")[1])
                encryptedFileName = getEncryptPath(path)+encryptedFileName+".txt"
                clientRequest = "READ_FILE"+"|"+userId+"|"+encryptedFileName + "|" + createHash(fileName)
                callPeerForRead(peer, clientRequest, encKey.split("|||")[0])


def deleteFile(fileName, userId):
    if verifyFileLock(createHash(fileName)):
        clientRequest = "DELETE_FILE"+"|"+userId+"|"+createHash(fileName)

        peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(createHash(fileName))
        peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
        
        if peer.split("|")[0] == "0":
            print(peer.split("|")[1])
        else:
            if callPeer(peer.split("|")[0], clientRequest, False):
                if not len(peer.split("|")) == 1:
                    for i, restPeer in enumerate(peer.split("|")[1:]):
                        callPeer(peer.split("|")[0], clientRequest, False)
                msg = fileIndexServer.performFileDelete(createHash(fileName))
                msg = crypto.fernetDecryption(msg, constants.peerCommEncKey)
                print(msg.split("|")[1])

 

def restoreFile(fileName, userId):
    clientRequest = "RESTORE_FILE"+"|"+userId+"|"+createHash(fileName)
    
    peer = fileIndexServer.getPeerURIToVerifyDelOrRestorePerm(createHash(fileName))
    peer = crypto.fernetDecryption(peer,constants.peerCommEncKey)
    
    if peer.split("|")[0] == "0":
        print(peer.split("|")[1])
    else:
        if callPeer(peer.split("|")[0], clientRequest, False):
            if not len(peer.split("|")) == 1:
                for i, restPeer in enumerate(peer.split("|")[1:]):
                    callPeer(peer.split("|")[0], clientRequest, False)
            msg = fileIndexServer.performFileRestore(createHash(fileName))
            msg = crypto.fernetDecryption(msg, constants.peerCommEncKey)
            print(msg.split("|")[1])



def goInsideDirectory(userId, directoryname):
    if verifyFileLock(createHash(directoryname)):
        permissionReq = "VERIFY_PERMISSION|"+userId+"|"+createHash(directoryname)+"|"+"r"
        peer = fileIndexServer.getPeerUriForRead(createHash(directoryname))
        peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
        if peer.split("|")[0] == "0":
            print(peer.split("|")[1])
        else:
            response = callPeer(peer, permissionReq, False)
            if not verifyFileAvailability(createHash(directoryname), True) and response:
                return True
            else:
                return False

def updateDirectoryName(userId, fileName, path):
    if verifyFileLock(createHash(fileName)):
        permissionReq = "VERIFY_PERMISSION|"+userId+"|"+createHash(fileName)+"|"+"r"
        peer = fileIndexServer.getPeerUriForRead(createHash(fileName))
        peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
        if peer.split("|")[0] == "0":
            print(peer.split("|")[1])
        else:
            response = callPeer(peer, permissionReq, False)
            if response:
                peer = fileIndexServer.lockFileRenameAndGetPeer(createHash(fileName))
                peer = crypto.fernetDecryption(peer, constants.peerCommEncKey)
                encKey = fileIndexServer.getEncryptionKey(createHash(fileName))
                encKey = crypto.fernetDecryption(encKey, constants.peerCommEncKey)
                encryptedFileName = crypto.fileNameEncryption(fileName.split("/")[-1], encKey.split("|||")[1])
                encryptedFileName = getEncryptPath(path)+encryptedFileName

                while 1:
                    print("Enter new name:")
                    newFileName = input()
                    if directoryNamePattern.fullmatch(newFileName.strip("\n")):
                        break
                    print("Invalid file name. File name should be alphanumeric.")
                newEncryptedFileName = crypto.fileNameEncryption(newFileName.strip("\n"), encKey.split("|||")[1])
                newEncryptedFileName = getEncryptPath(path) + newEncryptedFileName
                curr_time = str(datetime.datetime.now())
                clientRequest = "RENAME_DIRECTORY"+"|"+userId+"|"+encryptedFileName+"|"+createHash(fileName)+"|"+ newEncryptedFileName+"|"+ createHash(path+newFileName)+"|"+curr_time
                if peer.split("|")[0] == "0":
                    print(peer.split("|")[1])
                else:
                    for i,peer in enumerate(peer.split("|")):
                        print(peer)
                        callPeer(peer, clientRequest)
                    indexServReq = createHash(fileName) +"$"+ createHash(path+newFileName) +"$"+ curr_time
                    indexServReq = crypto.fernetEncryption(indexServReq, constants.fileIndexEncKey)
                    fileIndexServer.unlockFileRename(indexServReq)


def getEncryptPath(path):
    encPath = ""
    tempPath = ""
    for i, file in enumerate(path.strip("/").split("/")):
        tempPath = tempPath +file+ "/"
        print(tempPath)
        if file == "." or file == "db":
            encPath = encPath + file+ "/"
        else:
            encKey = fileIndexServer.getEncryptionKey(createHash(tempPath.rstrip("/")))
            encKey = crypto.fernetDecryption(encKey, constants.peerCommEncKey)
            encKey = encKey.split("|||")[1]
            encFileName = crypto.fileNameEncryption(file,encKey)
            encPath = encPath + encFileName + "/"
    return encPath

def listFilesInCurrentPath(userId,path):
    peerList = fileIndexServer.getAllPeers()
    peerList = crypto.fernetDecryption(peerList, constants.peerCommEncKey)
    clientRequest = "LIST_FILES|"+userId+"|"+getEncryptPath(path).rstrip("/")
    fileList = []
    fileList = fileList + callPeerForList(peerList.split("|")[0],clientRequest).split(",")
    print("--------------------------------------")
    if not len(fileList) == 0:
        print("Files available in current directory:")
        for i, file in enumerate(fileList):
            
            if not file == "":
                fileName,fileNameHash = file.split(" ")
                encKey = fileIndexServer.getEncryptionKey(fileNameHash)
                encKey = crypto.fernetDecryption(encKey, constants.peerCommEncKey)
                encKey = encKey.split("|||")[1]
                decFileName = crypto.fileNameDecryption(fileName.split(".")[0],encKey)
                if ".txt" in fileName:
                    decFileName = decFileName + ".txt"
                print(decFileName)
        





