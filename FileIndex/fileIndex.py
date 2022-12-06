import Pyro4
import json
import uuid
import datetime
import sys
sys.path.append("..")
import constants

index = {
    'fileInd':[
    ]
}

def updateFileIndex(fileNameHash, fileContentHash, timeStamp):
    for ind, peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash in fil["fileNameHash"]:
                index["fileInd"][ind]["index"][j]["timeStamp"] = timeStamp,
                index["fileInd"][ind]["index"][j]["fileContentHash"] = fileContentHash

def writeToFileIndex(jsonObject):
    fileIndex = {
            "id":uuid.uuid4().int,
            "peer":jsonObject["peerUri"],
            "nsHostIp":jsonObject["nsHostIp"],
            "fileCount":jsonObject["fileCount"],
            "index": jsonObject["index"]
        }
    
    index["fileInd"].append(fileIndex)
    print("----------------------")
    print(index["fileInd"])
    print("----------------------")
    return "1|Successfully updated file index"

def emptyFileIndex():
    index["fileInd"] = []

def addToFileIndex(fileObj):
    
    indexObj = {
        "fileNameHash":fileObj["fileNameHash"],
        "timeStamp":fileObj["timeStamp"],
        "fileContentHash":fileObj["fileContentHash"],
        "fileLock":fileObj["fileLock"],
        "fileDelete": False
    }

    for ind, peerContent in enumerate(index["fileInd"]):
        if peerContent["peer"] == fileObj["peerUri"]:
            index["fileInd"][ind]["fileCount"] = peerContent["fileCount"] + 1
            index["fileInd"][ind]["index"].append(indexObj)
    
    return "1|Successfully updated file index"



def verifyFileAvailability(jsonObject):
    msg = "1|File can be created"
    for ind,peerContent in enumerate(index["fileInd"]):
        if len(peerContent["index"]) != 0:
            for j,fil in enumerate(peerContent["index"]):
                if jsonObject["fileNameHash"] in fil["fileNameHash"]:
                        msg = "0|File already exists"
    
    return msg

def lockUnlockFileWrite(fileNameHash, flag):
    for ind, peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash in fil["fileNameHash"]:
                index["fileInd"][ind]["index"][j]["fileLock"] = flag


def getPeerURI(requestedURI, writeMethodFlag, fileNameHash):
    fileCount = 9999
    uri = ""
    for ind,peerContent in enumerate(index["fileInd"]):
        if writeMethodFlag:
            for j,fil in enumerate(peerContent["index"]):
                if fil["fileNameHash"] == fileNameHash:
                    uri = "|"+peerContent["peer"]+","+peerContent["nsHostIp"]
        else:
            if peerContent["fileCount"] < fileCount and peerContent["peer"] != requestedURI:
                fileCount = peerContent["fileCount"]
                uri = peerContent["peer"]+","+peerContent["nsHostIp"]

    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri
    

def getReadPeerURI(fileNameHash):
    uri = ""
    tempTimeStamp = datetime.datetime.now()
    tempTimeStamp = tempTimeStamp.replace(month=1, day=1) 

    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                if tempTimeStamp < datetime.datetime.strptime(fil["timeStamp"], '%Y-%m-%d %H:%M:%S.%f'):
                    uri = peerContent["peer"]+","+peerContent["nsHostIp"]
                    tempTimeStamp = datetime.datetime.strptime(fil["timeStamp"], '%Y-%m-%d %H:%M:%S.%f')
    
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

def getAllAvailablePeersUri():
    peerList = ""
    for ind,peerContent in enumerate(index["fileInd"]):
        peerList = peerContent["peer"]+","+peerContent["nsHostIp"]
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



@Pyro4.expose
class FileIndex(object):

    def __init__(self):
        # emptyFileIndex()
        pass

    def loadPeerFileIndex(self, jsonObject):
        return writeToFileIndex(jsonObject)

    def addToFileIndexJson(self, requestObj):
        return addToFileIndex(requestObj)

    def checkFileAvailability(self, jsonObject):
        return verifyFileAvailability(jsonObject)
    
    def getAvailablePeerURI(self, requestedURI):
        return getPeerURI(requestedURI, False, "")
    
    def lockAndGetPeerURI(self, fileNameHash):
        lockUnlockFileWrite(fileNameHash, True)
        return getPeerURI("", True, fileNameHash)
    
    def getPeerUriForRead(self, fileNameHash):
        return getReadPeerURI(fileNameHash)

    def unlockFileWrite(self, fileNameHash, fileContentHash, timeStamp):
        updateFileIndex(fileNameHash, fileContentHash, timeStamp)
        lockUnlockFileWrite(fileNameHash, False)

    def performFileDelete(self, fileNameHash):
        return updateDeleteFlag(fileNameHash, True)

    def performFileRestore(self, fileNameHash):
        return updateDeleteFlag(fileNameHash,False)

    def getPeerURIToVerifyDelOrRestorePerm(self, fileNameHash):
        return getReadPeerURI(fileNameHash)

    def getAllPeers(self):
        return getAllAvailablePeersUri()
    
    def checkIfFileIsDeleted(self, fileNameHash):
        return checkDeleteFlag(fileNameHash)

        


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
