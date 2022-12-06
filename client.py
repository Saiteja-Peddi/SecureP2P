from socket import *
from builtins import input
import sys
import fileOperationsCli as fileCli
import getpass
import Pyro4
import Pyro4.util
import constants
import re


dbDir = "./db"
fileNamePattern = re.compile("^([A-Za-z0-9])+(.txt)?$")
directoryNamePattern = re.compile("^([A-Za-z0-9])+$")
sys.excepthook = Pyro4.util.excepthook


def callAuthServer(authServer, clientRequest):
    
    serverResponse = authServer.authRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print(serverResponse.split("|")[1])
        return True
    else:
        print(serverResponse.split("|")[1])
        return False


def createUser(authServer, userId):
    while 1:
        password = getpass.getpass("Enter your password:\n")
        reEnterPassword = getpass.getpass("Re-Enter your password:\n")

        if password == reEnterPassword:
            break
        else:
            print("Passwords didn't match!")

    #If random hash is generating run below command
    #Mac: export PYTHONHASHSEED=0
    #Windows: $env:PYTHONHASHSEED=0
    hashedPassword = hash(password.encode())
    clientRequest = "CREATE_USER|"+userId+"|"+str(hashedPassword)

    return callAuthServer(authServer, clientRequest)


def authenticateUser(authServer, userId):
    password = getpass.getpass("Enter your password:\n")
    hashedPassword = hash(password.encode())
    clientRequest = "LOGIN_USER|"+userId+"|"+str(hashedPassword)
    return callAuthServer(authServer, clientRequest)


def provideLoginOptions():
    loginMsg = """
    Enter
    1 -> To Login
    2 -> To Sign up
    """
    print(loginMsg)

def provideFileOperationsMenu():
    menu ="""
    Command Menu:
    1. Create a file: create|<filename>|<permissions>
        Permission: r = read, rw = read & write, p = private
        Supports only directory and .txt file.
    2. Read a file: read|<filename>
    3. Write to a file: write|<filename>
    4. Delete a file: rmfile|<filename>
    5. Restore a file: restore|<filename>
    6. Create a directory: makedir|<directoryname>
    7. Go inside a directory: goindir|<directoryname> 
    8. Go back from a directory: gobackdir   
    9. Go to root directory: goroot
    10. List current working directory files: lscurr
    11. Exit from application: exit
    """
    #Implementation
    #1. For directory at clientside we maintain current working path all the time till the client logs out of the system.
    #2. The list root files will take the user to the top level of the file system so that user can start from the begining.
    print(menu)

#Checks user entered command


def checkCommandInput(cliCommand,create):
    if create:
        if len(cliCommand.split("|")) != 3:
            return False
        else:
            return True
    elif len(cliCommand.split("|")) != 2:
        return False
    else:
        return True


def main():
    cwd = "/"
    nameserver=Pyro4.locateNS(host = constants.autheServerHost)
    authIndexUri = nameserver.lookup("example.authServer")
    authServer = Pyro4.Proxy(authIndexUri)

    while 1:
        provideLoginOptions()
        opt = int(input())
        if opt == 1:
            #Login functionality
            print("Enter User Id:")
            userId = input()
            flag = authenticateUser(authServer, userId)
            if flag:
                break
            
        elif opt == 2:
            #Sign up functionality
            print("Enter User Id:")
            userId = input()
            flag = createUser(authServer, userId)
            if flag:
                break
        else:
            print("Please enter valid input")

    while 1:
        provideFileOperationsMenu()
        cliCommand = sys.stdin.readline()
        if "create" in cliCommand and checkCommandInput(cliCommand,True):
            _,fileName,permissions = cliCommand.split("|")
            if re.fullmatch(fileNamePattern, fileName):
                fileCli.createFile(dbDir+cwd+fileName.strip("\n"), permissions.strip("\n"), userId.strip("\n"))
            else:
                print("Invalid file type")
            

        elif "read" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.readFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

        elif "write" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.writeFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

        elif "rmfile" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.deleteFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

            # Below link contains how to delete an element from a json file
            # https://stackoverflow.com/questions/71764921/how-to-delete-an-element-in-a-json-file-python

        elif "restore" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.restoreFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

        elif "makedir"in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            if directoryNamePattern.fullmatch(fileName.strip("\n")):
                fileCli.createDirectory(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))
            else:
                print("Invalid file type")

        elif "goindir" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            if directoryNamePattern.fullmatch(fileName.strip("\n")):
                cwdUpdateFlag = fileCli.goInsideDirectory(dbDir+cwd+fileName.strip("\n"))
                if cwdUpdateFlag:
                    cwd = cwd +fileName.strip("\n")+"/"
                else:
                    print("Directory unavailable")
            else:
                print("Invalid filename entered")
        
        elif "gobackdir" in cliCommand:
            if "/" == cwd:
                print("You are in root folder")
            else:
                cwdList = cwd.split("/").pop()
                cwd = "/" + "/".join(cwdList)
                

        elif "lscurr" in cliCommand:
            fileCli.listFilesInCurrentPath(userId ,dbDir+cwd.rstrip("/"))

        elif "goroot" in cliCommand:
            cwd = "/"
            print("Current working directory updated to root folder")

        elif "exit" in cliCommand:
            sys.exit()

        else:
            print("Invalid Command")


if __name__ == "__main__":
    main()






