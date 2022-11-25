import Pyro4
import json
from .. import constants 
import uuid
import datetime



def updateFileIndexJson(fileNameHash, fileContentHash, timeStamp):
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        for ind,peerContent in enumerate(file_data["fileInd"]):
            for j,fil in enumerate(peerContent["index"]):
                if fileNameHash in fil["fileNameHash"]:
                    file_data["fileInd"][ind]["index"][j]["timeStamp"] = timeStamp,
                    file_data["fileInd"][ind]["index"][j]["fileContentHash"] = fileContentHash

        file.seek(0)
        json.dump(file_data, file, indent = 2)

def writeToFileIndexJson(jsonObject):
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        fileIndex = {
            "id":uuid.uuid4(),
            "peer":jsonObject.peerUri,
            "fileCount":jsonObject.fileCount,
            "index": jsonObject.index
        }
        file_data['fileInd'].append(fileIndex)
        file.seek(0)
        json.dump(file_data, file, indent = 2)
    return "1|Successfully updated file index"

def emptyFileIndexJson():
    with open('file_index.json','r+') as file:
        file_data = json.load(file)
        file_data['fileInd'] = []
        file.seek(0)
        json.dump(file_data, file, indent = 2)

def verifyFileAvailability(fileNameHash):
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        for ind,peerContent in enumerate(file_data["fileInd"]):
            for j,fil in enumerate(peerContent["index"]):
                if fileNameHash == fil["fileNameHash"]:
                    return "0|File already exists"
        
        file.seek(0)
        json.dump(file_data, file, indent = 2)
    
    return "1|File can be created"

def lockUnlockFileWrite(fileNameHash, flag):
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        for ind,peerContent in enumerate(file_data["fileInd"]):
            for j,fil in enumerate(peerContent["index"]):
                if fil["fileNameHash"] == fileNameHash:
                    file_data["fileInd"][ind]["index"][j]["fileLock"] = flag
    file.seek(0)
    json.dump(file_data, file, indent = 2)


def getPeerURI(requestedURI, writeMethodFlag, fileNameHash):
    fileCount = 9999
    uri = ""
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        for ind,peerContent in enumerate(file_data["fileInd"]):
            if writeMethodFlag:
                for j,fil in enumerate(peerContent["index"]):
                    if fil["fileNameHash"] == fileNameHash:
                        uri = "|"+peerContent["peer"]
            else:
                if peerContent["fileCount"] < fileCount and peerContent["peer"] != requestedURI:
                    fileCount = peerContent["fileCount"]
                    uri = peerContent["peer"]
        
        file.seek(0)
        json.dump(file_data, file, indent = 2)
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

def getReadPeerURI(fileNameHash):
    uri = ""
    tempTimeStamp = datetime.now().date().replace(month=1, day=1) 
    with open('file_index.json','r+') as file:
        file_data = json.load(file)

        for ind,peerContent in enumerate(file_data["fileInd"]):
            for j,fil in enumerate(peerContent["index"]):
                if fil["fileNameHash"] == fileNameHash and tempTimeStamp == "":
                    if tempTimeStamp - datetime.datetime.strptime(fil["timeStamp"], '%b %d %Y %I:%M:%S%p') < 0:
                        uri = peerContent["peer"]
                        tempTimeStamp = datetime.datetime.strptime(fil["timeStamp"], '%b %d %Y %I:%M:%S%p')
                    
        
        file.seek(0)
        json.dump(file_data, file, indent = 2)
    if uri == "":
        return "0|Unable to find a peer"
    else:
        return uri

@Pyro4.expose
class FileIndex(object):

    def __init__(self):
        emptyFileIndexJson()
        pass

    def loadPeerFileIndex(jsonObject):
        return writeToFileIndexJson(jsonObject)

    def checkFileAvailability(fileNameHash):
        return verifyFileAvailability(fileNameHash)
    
    def getAvailablePeerURI(requestedURI):
        return getPeerURI(requestedURI)
    
    def lockAndGetPeerURI(fileNameHash):
        lockUnlockFileWrite(fileNameHash, True)
        return getPeerURI("", True, fileNameHash)
    
    def getPeerUriForRead(fileNameHash):
        return getReadPeerURI(fileNameHash)

    def unlockFileWrite(fileNameHash, fileContentHash, timeStamp):
        updateFileIndexJson(fileNameHash, fileContentHash, timeStamp)
        lockUnlockFileWrite(fileNameHash, False)


        


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
