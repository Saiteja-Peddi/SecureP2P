from socket import *
from builtins import input
import sys
import fileOperationsCli as fileCli
import getpass
import Pyro4
import Pyro4.util
import constants
import re
import crypto
import hashlib
dbDir = "./db"
fileNamePattern = re.compile("^([A-Za-z0-9])+(.txt)$")
directoryNamePattern = re.compile("^([A-Za-z0-9])+$")
sys.excepthook = Pyro4.util.excepthook


# Calls authentication server
def callAuthServer(authServer, clientRequest):
    clientRequest = crypto.fernetEncryption(clientRequest, constants.authServerEncKey)
    serverResponse = authServer.authRequestHandler(clientRequest)
    if serverResponse.split("|")[0] == "1":
        print(serverResponse.split("|")[1])
        return True
    else:
        print(serverResponse.split("|")[1])
        return False


#Create user functionality
def createUser(authServer, userId):
    while 1:
        password = getpass.getpass("Enter your password:\n")
        reEnterPassword = getpass.getpass("Re-Enter your password:\n")

        if password == reEnterPassword:
            break
        else:
            print("Passwords didn't match!")
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    clientRequest = "CREATE_USER|"+userId+"|"+str(hashedPassword)

    return callAuthServer(authServer, clientRequest)

# Sign in functionality
def authenticateUser(authServer, userId):
    password = getpass.getpass("Enter your password:\n")
    hashedPassword = hashlib.sha256(password.encode()).hexdigest()
    clientRequest = "LOGIN_USER|"+userId+"|"+str(hashedPassword)
    return callAuthServer(authServer, clientRequest)


def provideLoginOptions():
    loginMsg = """
    Enter
    1 -> To Login
    2 -> To Sign up
    """
    print(loginMsg)

# Prints the menu where peer can execute the commands as presented below
def provideFileOperationsMenu():
    menu ="""
    Command Menu:
    1. Create a file: create|<filename>|<permissions>
        Permission: r = read, rw = read & write, p = private
        Supports only .txt file.
    2. Read a file: read|<filename>
    3. Write to a file: write|<filename>
    4. Delete a file: rmfile|<filename>
    5. Restore a file: restore|<filename>
    6. Create a directory: makedir|<directoryname>|<permissions>
        Permission: r = specified users, p = private
    7. Go inside a directory: goindir|<directoryname> 
    8. Rename directory: renamedir|<directoryname>
    9. Go back from a directory: gobackdir   
    10. Go to root directory: goroot
    11. List current working directory files: lscurr
    12. Exit from application: exit
    """
    print(menu)

#Checks command syntax
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

    #While loop for complete login functionality
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

    #While loop for complete file operations
    while 1:
        provideFileOperationsMenu()
        cliCommand = sys.stdin.readline()
        if "create" in cliCommand and checkCommandInput(cliCommand,True):
            _,fileName,permissions = cliCommand.split("|")
            if re.fullmatch(fileNamePattern, fileName) and permissions.strip("\n") in ["r", "rw", "p"]:
                fileCli.createFileOrDirectory(dbDir+cwd+fileName.strip("\n"), permissions.strip("\n"), userId.strip("\n"), dbDir+cwd, False)
            else:
                print("Invalid file type or permissions")
            
        elif "read" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.readFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"), dbDir+cwd)

        elif "write" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.writeFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"), dbDir+cwd)

        elif "rmfile" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.deleteFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

        elif "restore" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.restoreFile(dbDir+cwd+fileName.strip("\n"), userId.strip("\n"))

        elif "makedir"in cliCommand and checkCommandInput(cliCommand,True):
            _,fileName,permissions = cliCommand.split("|")
            if directoryNamePattern.fullmatch(fileName.strip("\n")) and permissions.strip("\n") in ["r", "p"]:
                fileCli.createFileOrDirectory(dbDir+cwd+fileName.strip("\n"), permissions.strip("\n"), userId.strip("\n"), dbDir+cwd, True)
            else:
                print("Invalid file type or permissions")

        elif "goindir" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            if directoryNamePattern.fullmatch(fileName.strip("\n")):
                cwdUpdateFlag = fileCli.goInsideDirectory(userId, dbDir+cwd+fileName.strip("\n"))
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
                cwdList = cwd.strip("/").split("/")
                cwd = "/" + "/".join(cwdList[:-1])
                
        elif "renamedir" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            if directoryNamePattern.fullmatch(fileName.strip("\n")):
                fileCli.updateDirectoryName(userId, dbDir+cwd+fileName.strip("\n"), dbDir+cwd)
            else:
                print("Invalid filename entered")

        elif "lscurr" in cliCommand:
            fileCli.listFilesInCurrentPath(userId ,dbDir+cwd.rstrip("/"))

        elif "goroot" in cliCommand:
            cwd = "/"
            print("Current working directory updated to root folder")

        elif "benchmark" in cliCommand:
            for i in range(1000, 10000):
                fileName = "bench"+str(i)+".txt"
                permissions = "p"
                fileCli.createFileOrDirectory(dbDir+cwd+fileName.strip("\n"), permissions.strip("\n"), userId.strip("\n"), dbDir+cwd, False)

        elif "exit" in cliCommand:
            sys.exit()

        else:
            print("Invalid Command")


if __name__ == "__main__":
    main()






