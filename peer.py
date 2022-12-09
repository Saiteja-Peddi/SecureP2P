import Pyro4
import json
import os
import constants
import datetime
import time
import crypto

peerName = constants.peerName
schedulerFlag = False
#To start name server enter below command in the shell
# python -m Pyro4.naming -n <your_hostname>




def loadFileIndexServer():
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    fileCount = 0
    index = []
    with open('file_perm.json','r') as file:
        file_data = json.load(file)
        fileCount = len(file_data["fileList"])
        if fileCount == 0:
            index = []
        else:
            for ind,fil in enumerate(file_data["fileList"]):
                if (not fil["fileNameHash"] == "") or (not fil["fileName"] == ""):
                    index.append(
                        {
                            "fileNameHash":fil["fileNameHash"],
                            "timeStamp":fil["timeStamp"],
                            "fileContentHash":fil["fileContentHash"],
                            "fileLock":False,
                            "fileDelete": False if fil["fileDelete"] == 0 else True
                        }
                    )

        # file.seek(0)
        # json.dump(file_data, file, indent = 4)
        file.close()

    indexServerPayload = {
        "peerUri" : peerName,
        "nsHostIp": constants.pyroHost,
        "fileCount":fileCount,
        "index":index,
    }
    indexServerPayload = crypto.fernetEncryption(str(indexServerPayload), constants.fileIndexEncKey)
    response = fileIndexServer.loadPeerFileIndex(indexServerPayload)
    response = crypto.fernetDecryption(response, constants.peerCommEncKey)
    print(response.split("|")[1])

def addToFileIndex(file):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    indexServerPayload = {
        "peerUri" :peerName,
        "fileNameHash":file["fileNameHash"],
        "fileContentHash":file["fileContentHash"],
        "timeStamp":file["timeStamp"],
        "fileLock": False,
        "fileDelete": False if file["fileDelete"] == 0 else True
    }
    indexServerPayload = crypto.fernetEncryption(str(indexServerPayload), constants.fileIndexEncKey)
    response = fileIndexServer.addToFileIndexJson(indexServerPayload)
    response = crypto.fernetDecryption(response, constants.peerCommEncKey)
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
    print(fileName)
    print(userId)
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileName in fil["fileName"] or fileName in fil["fileNameHash"]:
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

def verifyPermissionForKey(userId, fileNameHash, reqPerm):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileNameHash in fil["fileNameHash"]:
                if userId in fil["createdBy"] or (userId in fil["userList"] and reqPerm in fil["permission"]):
                    return "1|You can access key"
                else:
                    return "0|You cannot access key"

def createFile(userId, fileName, fileNameHash, fileContent, permissions, userList, timeStamp):
    if os.path.isfile(fileName):
        return "0|File already exists"
    else:

        if ".txt" in fileName:
            writeToFilePermJson(userId, fileName,  permissions, userList, fileNameHash, "", timeStamp)
            os.makedirs(os.path.dirname(fileName), exist_ok=True)
            file = open(fileName, "w")
            file.write(fileContent)
            file.close()
            return "1|File created successfully"
        else:
            writeToFilePermJson(userId, fileName, permissions, userList, fileNameHash, "", timeStamp)
            os.mkdir(fileName)
            return "1|Directory created successfully"


def checkFileAvailability(fileNameHash):
    msg ="1|File available"
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileNameHash == fil["fileNameHash"]:
                msg = "0|File already exists"
        file.close()
        return msg
       

def createDirectory(userId, fileName, fileNameHash, timeStamp):
    print(fileName)
    if os.path.isfile(fileName):
        return "0|File already exists"
    else:
        writeToFilePermJson(userId, fileName, "", "", fileNameHash, "", timeStamp)
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

def readFile(userId, fileName, fileNameHash):

    if verifyUserPermissions(userId,fileNameHash,False,True,False):
        file = open(fileName, "r")
        fileContent = ""
        for line in file.readlines():
            fileContent+=line+"\n"
        file.close()
        return "1|"+fileContent
    
    else:
        return "0|Access denied"

def deleteFile(userId, fileNameHash):

    if verifyUserPermissions(userId,fileNameHash,False,False,True):
        with open('file_perm.json','r+') as file:
            file_data = json.load(file)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileNameHash in fil["fileNameHash"]:
                    file_data["fileList"][ind]["fileDelete"] = 1
            file.seek(0)
            json.dump(file_data, file, indent = 4)
            file.close()   
        return "1|File can be deleted"
    else:
        return "0|Access denied"


def renameDirectory(oldFileName, oldFileNameHash, newFileName, newFileNameHash, timeStamp):
    msg = "0|Unable to rename the file"
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if oldFileNameHash in fil["fileNameHash"]:
                os.rename(oldFileName, newFileName)
                file_data["fileList"][ind]["fileNameHash"] = newFileNameHash
                file_data["fileList"][ind]["timeStamp"] = timeStamp
                file_data["fileList"][ind]["fileName"] = newFileName
                msg = "1|File rename successfull"
        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()

    return msg

def listFilesInPath(userId, path):
    nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
    fileIndexUri = nameserver.lookup("example.fileIndex")
    fileIndexServer = Pyro4.Proxy(fileIndexUri)
    msg = "0|Files unavailable in this peer"
    filesList = os.listdir(path)
    with open('file_perm.json','r') as file:
        file_data = json.load(file)
        for i, fileName in enumerate(filesList):
            if verifyUserPermissions(userId, fileName, False, True, False):
                for ind,fil in enumerate(file_data["fileList"]):
                    response = fileIndexServer.checkIfFileIsDeleted(fil["fileNameHash"])
                    response = crypto.fernetDecryption(response, constants.peerCommEncKey)
                    if fileName in fil["fileName"] and response.split("|")[1] == "False":
                        fileName = fileName + " " +fil["fileNameHash"]
                        if "1|" in msg:
                            msg = msg+","+fileName
                        else:
                            msg = "1|"+fileName
        file.close()
    return msg

def checkRestorePermission(userId, fileNameHash):
    if verifyUserPermissions(userId,fileNameHash,False,False,True):
        with open('file_perm.json','r+') as file:
            file_data = json.load(file)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileNameHash in fil["fileNameHash"]:
                    file_data["fileList"][ind]["fileDelete"] = 0
            file.seek(0)
            json.dump(file_data, file, indent = 4)
            file.close()   
        return "1|File can be restored"
    else:
        return "0|Access denied"

def permanentDelete():
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fil["fileDelete"] == 1:
                if os.path.isfile(fil["fileName"]):
                    print(fil["fileName"])
                    os.remove(fil["fileName"])
                    file_data["fileList"][ind]["fileName"] = ""
                    file_data["fileList"][ind]["fileNameHash"] = ""
                    file_data["fileList"][ind]["permission"] = ""
                    file_data["fileList"][ind]["createdBy"] = ""
                    file_data["fileList"][ind]["userList"] = []
        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.close()
    return "1|Peer cleaned"

@Pyro4.behavior(instance_mode="percall")
class Peer(object):
    loadFileIndexServer()

    def __init__(self):
        pass
    @Pyro4.expose
    def fileRequestHandler(self, cliMsg):
        cliMsg = crypto.fernetDecryption(cliMsg, constants.peerCommEncKey)
        if "CREATE_FILE" in cliMsg:
            _,userId, fileName, fileNameHash, fileContent, permissions, userList, timeStamp = cliMsg.split("|")
            message = createFile(userId.strip("\n"), fileName.strip("\n"), fileNameHash.strip("\n"), fileContent.strip("\n"), permissions.strip("\n"), userList, timeStamp)

        elif "WRITE_FILE" in cliMsg:
            _,userId, fileName, fileContent, fileContentHash, timeStamp = cliMsg.split("|")
            message = writeFile(userId.strip("\n"), fileName.strip("\n"), fileContent, fileContentHash, timeStamp)

        elif "READ_FILE" in cliMsg:
            _,userId, fileName, fileNameHash = cliMsg.split("|")
            message = readFile(userId, fileName, fileNameHash)

        elif "DELETE_FILE" in cliMsg:
            _,userId, fileNameHash = cliMsg.split("|")
            message = deleteFile(userId, fileNameHash)
        
        elif "RESTORE_FILE" in cliMsg:
            _,userId, fileNameHash = cliMsg.split("|")
            message = checkRestorePermission(userId, fileNameHash)

        elif "CREATE_DIRECTORY" in cliMsg:
            _,userId, fileName, fileNameHash, timeStamp = cliMsg.split("|")
            message = createDirectory(userId.strip("\n"), fileName.strip("\n"), fileNameHash.strip("\n"), timeStamp)

        elif "RENAME_DIRECTORY" in cliMsg:
            _,userId, oldFileName, oldFileNameHash, newFileName, newFileNameHash, timeStamp = cliMsg.split("|")
            message = renameDirectory(oldFileName, oldFileNameHash, newFileName, newFileNameHash, timeStamp)

        elif "LIST_FILES" in cliMsg:
            _,userId, path = cliMsg.split("|")
            message = listFilesInPath(userId, path)
        
        elif "VERIFY_PERMISSION" in cliMsg:
            _, userId, fileNameHash, reqPerm = cliMsg.split("|")
            message = verifyPermissionForKey(userId, fileNameHash, reqPerm)
        elif "PERMANENT_DELETE" in cliMsg:
            message = permanentDelete()
        
        elif "FILE_AVAILABLE" in cliMsg:
            _, fileName = cliMsg.split("|")
            message = checkFileAvailability(fileName)

        else:
            message = "0|Invalid option selected"

        message = crypto.fernetEncryption(message, constants.peerCommEncKey)
        return message

    @Pyro4.expose
    def verifyFilePermission(self, userId, fileNameHash):
        return verifyPermissionForKey(userId, fileNameHash)


    

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



