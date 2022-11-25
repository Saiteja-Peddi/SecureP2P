import Pyro4
import json
import rsa
import os
import shutil
import constants
import uuid
import datetime

peerName = "example.peer"




def loadFileIndexServer():
    fileIndexServer = Pyro4.Proxy("PYRONAME:example.fileIndex")
    fileCount = 0
    index = []
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            index.append(
                {
                    "fileNameHash":fil.fileNameHash,
                    "fileUid":fil.fileUid,
                    "timeStamp":fil.timeStamp,
                    "fileContentHash":fil.fileContentHash,
                    "fileLock":False
                }
            )

        fileCount = len(file_data["fileList"])
        file.seek(0)
        json.dump(file_data, file, indent = 4)

    indexServerPayload = {
        "peerUri" :peerName,
        "fileCount":fileCount,
        "index":index,
    }

    response = fileIndexServer.loadPeerFileIndex(indexServerPayload)
    print(response.split("|")[1])






def writeToFilePermJson(userId, fileName, permissions, userList, fileNameHash, fileContentHash, uid, timeStamp):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)

        fileMeta = {
            "fileName":fileName,
            "fileNameHash":fileNameHash,
            "fileContentHash":fileContentHash,
            "timeStamp":datetime.datetime.strptime(timeStamp, '%b %d %Y %I:%M:%S%p'),
            "permission":permissions.strip("\n"),
            "createdBy":userId,
            "userList":userList.split(","),
        }

        file_data['fileList'].append(fileMeta)
        file.seek(0)
        json.dump(file_data, file, indent = 4)

def updateFilePermJson(fileName, fileContentHash, timeStamp):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileName in fil["fileName"]:
                file_data["fileList"][ind]["timeStamp"] = datetime.datetime.strptime(timeStamp, '%b %d %Y %I:%M:%S%p')
                file_data["fileList"][ind]["fileContentHash"] = fileContentHash


        file.seek(0)
        json.dump(file_data, file, indent = 4)



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

def createFile(userId, fileName, permissions, userList, uid, timeStamp):

    if os.path.isfile(fileName):
        return "0|File already exists"
    else:
        writeToFilePermJson(userId, fileName, permissions, userList, str(hash(fileName)), "", uid, timeStamp)
        os.makedirs(os.path.dirname(fileName), exist_ok=True)
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

def readFile(userId, fileName, path):

    if verifyUserPermissions(userId,fileName,path,False,True,False):
        file = open(path+"/"+fileName, "r")
        fileContent = ""
        for line in file.readlines():
            fileContent+=line+"\n"
        file.close()
        return "1|"+fileContent
    
    else:
        return "0|Access denied"

def deleteFile(userId, fileName, path):

    if verifyUserPermissions(userId,fileName,path,False,False,True):
        source = path + "/" + fileName
        destination = "./db/backup/"+fileName
        with open('file_perm.json', "r") as f:
            file_data = json.load(f)
            for ind,fil in enumerate(file_data["fileList"]):
                if fileName in fil["fileName"] and path in fil["path"]:
                    file_data["fileList"].pop(ind)
        
        with open('file_perm.json', "w") as f:
            json.dump(file_data,f)
        shutil.move(source, destination)
        return "1|File deleted successfully"
    
    else:
        return "0|Access denied"


@Pyro4.expose
class Peer(object):


    def __init__(self):
        loadFileIndexServer()
        pass


    def fileRequestHandler(self, cliMsg):

        if "CREATE_FILE" in cliMsg:
            _,userId, fileName, permissions, userList, uid, timeStamp = cliMsg.split("|")
            message = createFile(userId.strip("\n"), fileName.strip("\n"), permissions.strip("\n"), userList, uid, timeStamp)

        elif "WRITE_FILE" in cliMsg:
            _,userId, fileName, path, fileContent, fileContentHash, timeStamp = cliMsg.split("|")
            message = writeFile(userId.strip("\n"), fileName.strip("\n"), path.strip("\n"), fileContent, fileContentHash, timeStamp)

        elif "READ_FILE" in cliMsg:
            _,userId, fileName, path = cliMsg.split("|")
            message = readFile(userId.strip("\n"), fileName.strip("\n"), path.strip("\n"))

        elif "DELETE_FILE" in cliMsg:
            _,userId, fileName, path = cliMsg.split("|")
            message = deleteFile(userId.strip("\n"), fileName.strip("\n"), path.strip("\n"))
        
        elif "RESTORE_FILE" in cliMsg:
            print("Restore a file")

        elif "CREATE_DIRECTORY" in cliMsg:
            print("Create directory")
        
        elif "DELETE_DIRECTORY" in cliMsg:
            print("Delete a directory")

        elif "GOIN_DIRECTORY" in cliMsg:
            print("Delete a directory")

        elif "LIST_ROOT" in cliMsg:
            print("Lists root folder files")

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



