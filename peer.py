import Pyro4
import json
import rsa
import os
import constants
import datetime
import time

peerName = constants.peerName
schedulerFlag = False
#To start name server enter below command in the shell
# python -m Pyro4.naming -n <your_hostname>

nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
fileIndexUri = nameserver.lookup("example.fileIndex")
fileIndexServer = Pyro4.Proxy(fileIndexUri)

def loadFileIndexServer():

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
                        "fileDelete": False if fil["fileDelete"] == 0 else True
                    }
                )

        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()

    indexServerPayload = {
        "peerUri" : peerName,
        "nsHostIp": constants.pyroHost,
        "fileCount":fileCount,
        "index":index,
    }

    response = fileIndexServer.loadPeerFileIndex(indexServerPayload)
    print(response.split("|")[1])

def addToFileIndex(file):
    indexServerPayload = {
        "peerUri" :peerName,
        "fileNameHash":file["fileNameHash"],
        "fileContentHash":file["fileContentHash"],
        "timeStamp":file["timeStamp"],
        "fileLock": False,
        "fileDelete": False if file["fileDelete"] == 0 else True
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
            "fileDelete":0
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
                file_data["fileList"][ind]["timeStamp"] = str(datetime.datetime.strptime(timeStamp, '%Y-%m-%d %H:%M:%S.%f'))
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
                    if userId in fil["createdBy"] or (userId in fil["userList"] and "rw" in fil["permission"]):
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
        file = open(fileName, "w")
        file.write("Please enter file content")
        file.close()
        return "1|File created successfully"

def createDirectory(userId, fileName, timeStamp):
    print(fileName)
    if os.path.isfile(fileName):
        return "0|File already exists"
    else:
        writeToFilePermJson(userId, fileName, "", "", str(hash(fileName)), "", timeStamp)
        os.mkdir(fileName)
        return "1|Directory created successfully"

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
        with open('file_perm.json','r+') as file:
            file_data = json.load(file)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileName in fil["fileName"]:
                    file_data["fileList"][ind]["fileDelete"] = 1
            file.seek(0)
            json.dump(file_data, file, indent = 4)
            file.close()   
        return "1|File can be deleted"
    else:
        return "0|Access denied"


def listFilesInPath(userId, path):
    msg = "0|Files unavailable in this peer"
    filesList = os.listdir(path)
    for i, file in enumerate(filesList):
        if verifyUserPermissions(userId, file, False, True, False) and fileIndexServer.checkIfFileIsDeleted(str(hash(path+"/"+file))).split("|")[1] == "False":
            if "1|" in msg:
                msg = msg+","+file
            else:
                msg = "1|"+file
    return msg

def checkRestorePermission(userId, fileName):
    if verifyUserPermissions(userId,fileName,False,False,True):
        with open('file_perm.json','r+') as file:
            file_data = json.load(file)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileName in fil["fileName"]:
                    file_data["fileList"][ind]["fileDelete"] = 0
            file.seek(0)
            json.dump(file_data, file, indent = 4)
            file.close()   
        return "1|File can be restored"
    else:
        return "0|Access denied"

def deleteScheduler():
    global schedulerFlag
    if schedulerFlag:
        return
    while True:
        schedulerFlag = True
        with open('file_perm.json','r+') as file:
            file_data = json.load(file)
            for ind,fil in enumerate(file_data["fileList"]):
                if fil["fileDelete"] == 1:
                    if os.path.isfile(fil["fileName"]):
                        os.remove(fil["fileName"])
                        file_data.pop(file_data["fileList"][ind])
            file.seek(0)
            json.dump(file_data, file, indent = 4)
            file.close()
        time.sleep(900)

@Pyro4.expose
class Peer(object):
    loadFileIndexServer()
    # deleteScheduler()

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
            _,userId, fileName = cliMsg.split("|")
            message = checkRestorePermission(userId, fileName)

        elif "CREATE_DIRECTORY" in cliMsg:
            _,userId, fileName, timeStamp = cliMsg.split("|")
            message = createDirectory(userId.strip("\n"), fileName.strip("\n"), timeStamp)

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



