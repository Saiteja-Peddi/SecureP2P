import Pyro4
import json
import rsa
import os
import shutil
import constants
import uuid
import datetime

peerName = constants.peerName


#To start name server enter below command in the shell
# python -m Pyro4.naming -n <your_hostname>

def loadFileIndexServer():
    print("Loading file index server")
    fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")

    fileCount = 0
    index = []
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        fileCount = len(file_data["fileList"])
        if fileCount == 0:
            index = []
        else:
            for ind,fil in enumerate(file_data["fileList"]):
                index.append(
                    {
                        "fileNameHash":fil["fileNameHash"],
                        "timeStamp":fil["timeStamp"],
                        "fileContentHash":fil["fileContentHash"],
                        "fileLock":False,
                        "fileDelete": False
                    }
                )

        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()

    indexServerPayload = {
        "peerUri" : peerName,
        "fileCount":fileCount,
        "index":index,
    }

    response = fileIndexServer.loadPeerFileIndex(indexServerPayload)
    print(response.split("|")[1])

def addToFileIndex(file):
    fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
    indexServerPayload = {
        "peerUri" :peerName,
        "fileNameHash":file["fileNameHash"],
        "fileContentHash":file["fileContentHash"],
        "timeStamp":file["timeStamp"],
        "fileLock": False,
    }

    response = fileIndexServer.addToFileIndexJson(indexServerPayload)
    print(response.split("|")[1])



def writeToFilePermJson(userId, fileName, permissions, userList, fileNameHash, fileContentHash, timeStamp):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)

        fileMeta = {
            "fileName":fileName,
            "fileNameHash":fileNameHash,
            "fileContentHash":fileContentHash,
            "timeStamp":timeStamp,
            "permission":permissions.strip("\n"),
            "createdBy":userId,
            "userList":userList.split(","),
        }

        addToFileIndex(fileMeta)
        file_data['fileList'].append(fileMeta)
        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()

def updateFilePermJson(fileName, fileContentHash, timeStamp):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileName in fil["fileName"]:
                file_data["fileList"][ind]["timeStamp"] = datetime.datetime.strptime(timeStamp, '%b %d %Y %I:%M:%S.%f')
                file_data["fileList"][ind]["fileContentHash"] = fileContentHash


        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()



def verifyUserPermissions(userId, fileName, checkWrite, checkRead, checkDelete):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileName in fil["fileName"]:
                if checkWrite:
                    if userId in fil["createdBy"]:
                        return True
                    else:
                        return False
                elif checkRead:
                    if userId in fil["createdBy"] or (userId in fil["userList"] and "r" in fil["permission"]):
                        return True
                    else:
                        return False
                elif checkDelete:
                    if userId in fil["createdBy"]:
                        return True
                    else:
                        return False
                else:
                    return False

        file.close()

def createFile(userId, fileName, permissions, userList, timeStamp):

    if os.path.isfile(fileName):
        return "0|File already exists"
    else:
        writeToFilePermJson(userId, fileName, permissions, userList, str(hash(fileName)), "", timeStamp)
        os.makedirs(os.path.dirname(fileName), exist_ok=True)
        if ".txt" in fileName:
            file = open(fileName, "w")
            file.write("Please enter file content")
            file.close()
        return "1|File created successfully"


def writeFile(userId, fileName, fileContent, fileContentHash, timeStamp):

    if verifyUserPermissions(userId,fileName,True,False,False):
        file = open(fileName, "w")
        file.write(fileContent)
        file.close()
        updateFilePermJson(fileName, fileContentHash, timeStamp)
        return "1|File write successfull"
    
    else:
        return "0|Access denied"

def readFile(userId, fileName):

    if verifyUserPermissions(userId,fileName,False,True,False):
        file = open(fileName, "r")
        fileContent = ""
        for line in file.readlines():
            fileContent+=line+"\n"
        file.close()
        return "1|"+fileContent
    
    else:
        return "0|Access denied"

def deleteFile(userId, fileName):

    if verifyUserPermissions(userId,fileName,False,False,True):
        source = fileName
        destination = "./db/backup/"+fileName
        with open('file_perm.json', "r") as f:
            file_data = json.load(f)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileName in fil["fileName"]:
                    file_data["fileList"].pop(ind)
        f.close()
        with open('file_perm.json', "w") as f:
            json.dump(file_data,f)
        f.close()

        fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
        shutil.move(source, destination)
        msg = fileIndexServer.updateFileDeleteInIndex(peerName, str(hash(fileName)))
        return msg
    
    else:
        return "0|Access denied"


def listFilesInPath(userId, path):
    print("List files in given path that belongs to given user")

@Pyro4.expose
class Peer(object):
    loadFileIndexServer()

    def __init__(self):
        pass

    def fileRequestHandler(self, cliMsg):

        if "CREATE_FILE" in cliMsg:
            _,userId, fileName, permissions, userList, timeStamp = cliMsg.split("|")
            message = createFile(userId.strip("\n"), fileName.strip("\n"), permissions.strip("\n"), userList, timeStamp)

        elif "WRITE_FILE" in cliMsg:
            _,userId, fileName, fileContent, fileContentHash, timeStamp = cliMsg.split("|")
            message = writeFile(userId.strip("\n"), fileName.strip("\n"), fileContent, fileContentHash, timeStamp)

        elif "READ_FILE" in cliMsg:
            _,userId, fileName = cliMsg.split("|")
            message = readFile(userId, fileName)

        elif "DELETE_FILE" in cliMsg:
            _,userId, fileName = cliMsg.split("|")
            message = deleteFile(userId, fileName)
        
        elif "RESTORE_FILE" in cliMsg:
            print("Restore a file")

        elif "GOIN_DIRECTORY" in cliMsg:
            print("Delete a directory")

        elif "LIST_FILES" in cliMsg:
            _,userId, path = cliMsg.split("|")
            message = listFilesInPath(userId, path)

        else:
            message = "0|Invalid option selected"

        return message

    

def main():
    Pyro4.Daemon.serveSimple(
            {
                Peer: peerName
            },
            ns = True,
            host = constants.pyroHost,
            port = constants.peerPort) 



if __name__ == "__main__":
    main()



