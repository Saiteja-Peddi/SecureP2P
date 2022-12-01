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

def updateFileIndexJson(fileNameHash, fileContentHash, timeStamp):
    for ind, peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash in fil["fileNameHash"]:
                index["fileInd"][ind]["index"][j]["timeStamp"] = timeStamp,
                index["fileInd"][ind]["index"][j]["fileContentHash"] = fileContentHash

def writeToFileIndexJson(jsonObject):
    fileIndex = {
            "id":uuid.uuid4().int,
            "peer":jsonObject["peerUri"],
            "fileCount":jsonObject["fileCount"],
            "index": jsonObject["index"]
        }
    index["fileInd"].append(fileIndex)

    return "1|Successfully updated file index"

def emptyFileIndexJson():
    index["fileInd"] = []

def addToFileIndex(fileObj):
    
    indexObj = {
        "fileNameHash":fileObj["fileNameHash"],
        "timeStamp":fileObj["timeStamp"],
        "fileContentHash":fileObj["fileContentHash"],
        "fileLock":fileObj["fileLock"],
        "fileDeleteFlag": False
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
                    uri = "|"+peerContent["peer"]
        else:
            if peerContent["fileCount"] < fileCount and peerContent["peer"] != requestedURI:
                fileCount = peerContent["fileCount"]
                uri = peerContent["peer"]

    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

def updateDeleteFlag(requestedURI, fileNameHash):
    msg = "0|Error: Unable to update file delete"
    
    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fileNameHash in fil["fileNameHash"] and peerContent["peer"] in requestedURI:
                index["fileInd"][ind]["index"][j]["fileDeleteFlag"] = True
                msg = "1|File delete successful"

    return msg
    

def getReadPeerURI(fileNameHash):
    uri = ""
    tempTimeStamp = datetime.now().date().replace(month=1, day=1) 

    for ind,peerContent in enumerate(index["fileInd"]):
        for j,fil in enumerate(peerContent["index"]):
            if fil["fileNameHash"] == fileNameHash:
                if tempTimeStamp - datetime.datetime.strptime(fil["timeStamp"], '%b %d %Y %I:%M:%S.%f') < 0:
                    uri = peerContent["peer"]
                    tempTimeStamp = datetime.datetime.strptime(fil["timeStamp"], '%b %d %Y %I:%M:%S.%f')
    
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

@Pyro4.expose
class FileIndex(object):

    def __init__(self):
        emptyFileIndexJson()
        pass

    def loadPeerFileIndex(self, jsonObject):
        return writeToFileIndexJson(jsonObject)

    def addToFileIndexJson(self, requestObj):
        return addToFileIndex(requestObj)

    def checkFileAvailability(self, jsonObject):
        return verifyFileAvailability(jsonObject)
    
    def getAvailablePeerURI(self, requestedURI):
        return getPeerURI(requestedURI)
    
    def lockAndGetPeerURI(self, fileNameHash):
        lockUnlockFileWrite(fileNameHash, True)
        return getPeerURI("", True, fileNameHash)
    
    def getPeerUriForRead(self, fileNameHash):
        return getReadPeerURI(fileNameHash)

    def unlockFileWrite(self, fileNameHash, fileContentHash, timeStamp):
        updateFileIndexJson(fileNameHash, fileContentHash, timeStamp)
        lockUnlockFileWrite(fileNameHash, False)

    def getPeerURIForDelete(self, fileNameHash):
        return getPeerURI("", True, fileNameHash)

    def updateFileDeleteInIndex(self, requestedURI, fileNameHash):
        return updateDeleteFlag(requestedURI, fileNameHash)

        


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
