import Pyro4
import json
import uuid
import datetime
import sys
sys.path.append("..")
import constants
import crypto


index = {
    'fileInd':[
    ]
}

global keys
with open('keys.txt','r') as keysData:
    keys = keysData.read()
    keys = json.loads(str(keys).replace("'", "\""))
    
def loadToKeysFile():
    with open('keys.txt','w') as data: 
        data.seek(0)
        data.write(str(keys))
        data.close()



def updateFileIndex(fileNameHash, fileContentHash, timeStamp):
    for ind, peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash in fil["fileNameHash"]:
                index["fileInd"][ind]["index"][j]["timeStamp"] = timeStamp,
                index["fileInd"][ind]["index"][j]["fileContentHash"] = fileContentHash
    
# Writes to file index about peer information initially while every peer connects to network
def writeToFileIndex(jsonObject):
    for ind, peerContent in enumerate(index["fileInd"]):
        if peerContent["nsHostIp"] == jsonObject["nsHostIp"]:
            del index['fileInd'][ind]
    fileIndex = {
            "id":uuid.uuid4().int,
            "peer":jsonObject["peerUri"],
            "nsHostIp":jsonObject["nsHostIp"],
            "fileCount":jsonObject["fileCount"],
            "index": jsonObject["index"]
        }
    
    index["fileInd"].append(fileIndex)
    return "1|Successfully updated file index"
    

def emptyFileIndex():
    index["fileInd"] = []

# Adds a record about a file containing in a peer when a file is created
def addToFileIndex(fileObj):
    
    indexObj = {
        "fileNameHash":fileObj["fileNameHash"],
        "timeStamp":fileObj["timeStamp"],
        "fileContentHash":fileObj["fileContentHash"],
        "fileLock":fileObj["fileLock"],
        "fileDelete": False
    }
    appendFlag = True
    for ind, peerContent in enumerate(index["fileInd"]):
        if peerContent["peer"] == fileObj["peerUri"]:
            for j,fil in enumerate(peerContent["index"]):
                if fileObj["fileNameHash"] in fil["fileNameHash"]:
                    appendFlag = False
            if appendFlag:
                index["fileInd"][ind]["fileCount"] = peerContent["fileCount"] + 1
                index["fileInd"][ind]["index"].append(indexObj)
    return "1|Successfully updated file index"



def verifyFileAvailability(fileNameHash):
    msg = "1|File can be created"
    for ind,peerContent in enumerate(index["fileInd"]):
        if len(peerContent["index"]) != 0:
            for j,fil in enumerate(peerContent["index"]):
                if fileNameHash in fil["fileNameHash"]:
                        msg = "0|File already exists"
    return msg

# Lock and Unlock mechanism while user is writing
def lockUnlockFileWrite(fileNameHash, flag):
    for ind, peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash == fil["fileNameHash"]:
                index["fileInd"][ind]["index"][j]["fileLock"] = flag

# Sends connection details to the peer about every peer which contains file 
def getPeerURI(requestedURI, writeMethodFlag, fileNameHash):
    fileCount = 9999
    uri = ""
    for ind,peerContent in enumerate(index["fileInd"]):
        if writeMethodFlag:
            for j,fil in enumerate(peerContent["index"]):
                if fil["fileNameHash"] == fileNameHash:
                    uri = uri + peerContent["peer"]+","+peerContent["nsHostIp"]
                    if not ind == len(index["fileInd"])-1:
                        uri = uri + "|"
        else:
            if peerContent["fileCount"] < fileCount and peerContent["peer"] != requestedURI:
                fileCount = peerContent["fileCount"]
                uri = peerContent["peer"]+","+peerContent["nsHostIp"]

    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri
    
# Sends connection details of a peer to read the file
def getReadPeerURI(fileNameHash):
    uri = ""
    tempTimeStamp = datetime.datetime.now()
    tempTimeStamp = tempTimeStamp.replace(month=1, day=1) 

    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                uri = peerContent["peer"]+","+peerContent["nsHostIp"]
    
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

# Sends connection details of a peer to delete the file
def getDeletePeersURI(fileNameHash):
    uri =""
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                uri = uri + peerContent["peer"]+","+peerContent["nsHostIp"]
                if not ind == len(index["fileInd"])-1:
                    uri += "|"
    
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

# Sends connection details of a all peers 
def getAllAvailablePeersUri():
    peerList = ""
    for ind,peerContent in enumerate(index["fileInd"]):
        peerList = peerList + peerContent["peer"]+","+peerContent["nsHostIp"]
        if not ind == len(index["fileInd"])-1:
            peerList += "|"
    return peerList


def updateDeleteFlag(fileNameHash, flag):
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                index["fileInd"][ind]["index"][j]["fileDelete"] = flag
    
    if flag:
        msg="1|File deleted successfully"
    else:
        msg="1|File restored successfully"
    return msg

def checkDeleteFlag(fileNameHash):
    msg = "0|File cannot be found"
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                if fil["fileDelete"] == True:
                    msg = "1|True"
                else:
                    msg = "1|False"
    return msg            

def storeKey(fileNameHash, key):
    keys[fileNameHash] = key
    loadToKeysFile()
    return "1|Key stored successfully"


def getKey(fileNameHash):
    return keys[fileNameHash]


def checkLock(fileNameHash):
    msg = "0|Invalid Filename"
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                if fil["fileLock"]:
                    return "0|File can't be accessed"
                else:
                    return "1|File can be accessed"
    return msg

# Updates directory name metadata when renamed
def updateFileNameHash(oldFileNameHash, newFileNameHash, curr_time):
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == oldFileNameHash:
                index["fileInd"][ind]["index"][j]["fileNameHash"] = newFileNameHash
                index["fileInd"][ind]["index"][j]["timeStamp"] = curr_time
    keys[newFileNameHash] = keys[oldFileNameHash]
    del keys[oldFileNameHash]
    loadToKeysFile()

# Removes all deleted files data
def removeDeletedFilesData():
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileDelete"] == True:
                fileNameHash = fil["fileNameHash"]
                keys[fileNameHash] = ""
                index["fileInd"][ind]["index"][j] = {
                    "fileNameHash":"",
                    "timeStamp":"",
                    "fileContentHash":"",
                    "fileLock":"",
                    "fileDelete": False
                }
                loadToKeysFile()
    return "1|Permanently removed sofar deleted files"


@Pyro4.behavior(instance_mode="percall")
class FileIndex(object):

    def __init__(self):
        # emptyFileIndex()
        pass

    @Pyro4.expose
    def loadPeerFileIndex(self, jsonObject):
        jsonObject = crypto.fernetDecryption(jsonObject, constants.fileIndexEncKey)
        jsonObject = eval(jsonObject)
        response = writeToFileIndex(jsonObject)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def addToFileIndexJson(self, requestObj):
        requestObj = crypto.fernetDecryption(requestObj, constants.fileIndexEncKey)
        requestObj = eval(requestObj)
        response = addToFileIndex(requestObj)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def checkFileAvailability(self, fileNameHash):
        response = verifyFileAvailability(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)
    
    # @Pyro4.expose
    # def getAvailablePeerURI(self, requestedURI):
    #     return getPeerURI(requestedURI, False, "")
    
    @Pyro4.expose
    def lockAndGetPeerURI(self, fileNameHash):
        lockUnlockFileWrite(fileNameHash, True)
        response = getPeerURI("", True, fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def getPeerUriForRead(self, fileNameHash):
        response = getReadPeerURI(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def unlockFileWrite(self, request):
        print("Unlock called in index")
        request = crypto.fernetDecryption(request, constants.fileIndexEncKey)
        fileNameHash, fileContentHash, timeStamp = request.split("$")
        updateFileIndex(fileNameHash, fileContentHash, timeStamp)
        lockUnlockFileWrite(fileNameHash, False)

    @Pyro4.expose
    def performFileDelete(self, fileNameHash):
        response = updateDeleteFlag(fileNameHash, True)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def performFileRestore(self, fileNameHash):
        response = updateDeleteFlag(fileNameHash,False)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def getPeerURIToVerifyDelOrRestorePerm(self, fileNameHash):
        response = getDeletePeersURI(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def getAllPeers(self):
        response = getAllAvailablePeersUri()
        return crypto.fernetEncryption(response, constants.peerCommEncKey)
    
    @Pyro4.expose
    def checkIfFileIsDeleted(self, fileNameHash):
        response = checkDeleteFlag(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def storeEncryptionKey(self, request):
        request = crypto.fernetDecryption(request, constants.fileIndexEncKey)
        fileNameHash, key = request.split(" ")
        response = storeKey(fileNameHash, key)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)
    
    @Pyro4.expose
    def getEncryptionKey(self, fileNameHash):
        response = getKey(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def checkFileLock(self, fileNameHash):
        response = checkLock(fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    @Pyro4.expose
    def lockFileRenameAndGetPeer(self, fileNameHash):
        lockUnlockFileWrite(fileNameHash, True)
        response = getPeerURI("", True, fileNameHash)
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

    
    @Pyro4.expose
    def unlockFileRename(self, request):
        request = crypto.fernetDecryption(request, constants.fileIndexEncKey)
        oldFileNameHash, newFileNameHash, timeStamp = request.split("$")
        updateFileNameHash(oldFileNameHash, newFileNameHash, timeStamp)
        lockUnlockFileWrite(newFileNameHash, False)

    @Pyro4.expose
    def permanentDelete(self):
        response = removeDeletedFilesData()
        return crypto.fernetEncryption(response, constants.peerCommEncKey)

def main():
    Pyro4.Daemon.serveSimple(
            {
                FileIndex: "example.fileIndex"
            },
            ns = True,
            host = constants.pyroHost,
            port = constants.fileIndexPort) 



if __name__ == "__main__":
    main()
