import Pyro4
import json
import rsa
import os
import shutil






def writeToFilePermJson(userId, fileName, path, permissions, userList):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)

        fileMeta = {
            "fileName":fileName,
            "permission":permissions.strip("\n"),
            "createdBy":userId,
            "userList":userList.split(","),
            "path":path
        }

        file_data['fileList'].append(fileMeta)
        file.seek(0)
        json.dump(file_data, file, indent = 4)


def verifyUserPermissions(userId, fileName, path, checkWrite, checkRead, checkDelete):
    with open('file_perm.json','r+') as file:
        file_data = json.load(file)
        for ind,fil in enumerate(file_data["fileList"]):
            if fileName in fil["fileName"] and path in fil["path"]:
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

def createFile(userId, fileName, path, permissions, userList):

    if os.path.isfile(path+"/"+fileName):
        return "0|File already exists"
    else:
        writeToFilePermJson(userId, fileName, path, permissions, userList)
        file = open(path+"/"+fileName, "w")
        file.write("Please enter file content")
        file.close()
        return "1|File created successfully"


def writeFile(userId, fileName, path, fileContent):

    if verifyUserPermissions(userId,fileName,path,True,False,False):
        file = open(path+"/"+fileName, "w")
        file.write(fileContent)
        file.close()
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
        pass


    def fileRequestHandler(self, cliMsg):

        if "CREATE_FILE" in cliMsg:
            _,userId, fileName, path, permissions, userList = cliMsg.split("|")
            message = createFile(userId.strip("\n"), fileName.strip("\n"), path.strip("\n"), permissions.strip("\n"), userList)

        elif "WRITE_FILE" in cliMsg:
            _,userId, fileName, path, fileContent = cliMsg.split("|")
            message = writeFile(userId.strip("\n"), fileName.strip("\n"), path.strip("\n"), fileContent)

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
                Peer: "example.peer"
            },
            ns = True,
            host = "192.168.0.33",
            port = 9001) 



if __name__ == "__main__":
    main()



