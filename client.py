from socket import *
from builtins import input
import sys
import fileOperationsCli as fileCli
import getpass
import Pyro4
import Pyro4.util


dbAddress = "localhost"
dbPort = 9000
authAddress = 'localhost'
authPort = 9000
cwd = "./db"


sys.excepthook = Pyro4.util.excepthook

def socketConnection():
    #AF_INET represents which family address type belongs to.
    cliSock = socket(AF_INET, SOCK_STREAM)
    return cliSock 

def callAuthServer(clientRequest):
    #Client creating api request to server
    print ("Calling Server")
    cliSoc = socketConnection()
    cliSoc.connect((authAddress,authPort))
    cliSoc.send(clientRequest.encode())
    serverResponse = cliSoc.recv(1024)
    serverResponse = serverResponse.decode()
    cliSoc.close()
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

    return authServer.authRequestHandler(clientRequest)

    # return callAuthServer(clientRequest)


def authenticateUser(authServer, userId):
    password = getpass.getpass("Enter your password:\n")
    hashedPassword = hash(password.encode())
    clientRequest = "LOGIN_USER|"+userId+"|"+str(hashedPassword)
    

    return authServer.authRequestHandler(clientRequest)
    # return callAuthServer(clientRequest)


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
        Supports only .txt file
    2. Read a file: read|<filename>
    3. Write to a file: write|<filename>
    4. Delete a file: rmfile|<filename>
    5. Restore a file: restore|<filename>
    6. Create a Directory: crdir|<directoryname>
    7. Delete a Directory: rmdir|<directoryname>
    8. Go inside a directory: goindir|<directoryname> 
        To go back enter ".." in <directoryname>
    9. List root files: lsroot
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

    authServer = Pyro4.Proxy("PYRONAME:example.authServer")

    while 1:
        provideLoginOptions()
        opt = int(input())
        if opt == 1:
            #Login functionality
            print("Enter User Id:")
            userId = input()
            flag = authenticateUser(authServer, userId)
            print(flag)
            if flag:
                break
            
        elif opt == 2:
            #Sign up functionality
            print("Enter User Id:")
            userId = input()
            flag = createUser(authServer, userId)
            print(flag)
            if flag:
                break
        else:
            print("Please enter valid input")
    
    provideFileOperationsMenu()

    peer = Pyro4.Proxy("PYRONAME:example.peer")

    while 1:
        cliCommand = sys.stdin.readline()
        if "create" in cliCommand and checkCommandInput(cliCommand,True):
            _,fileName,permissions = cliCommand.split("|")
            fileCli.createFile(peer, fileName, cwd, permissions, userId)

        elif "read" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.readFile(peer, fileName, cwd, userId)

        elif "write" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.writeFile(peer, fileName, cwd, userId)

        elif "rmfile" in cliCommand and checkCommandInput(cliCommand,False):
            _,fileName = cliCommand.split("|")
            fileCli.deleteFile(peer, fileName, cwd, userId)

            # Below link contains how to delete an element from a json file
            # https://stackoverflow.com/questions/71764921/how-to-delete-an-element-in-a-json-file-python
        
        elif "rmdir" in cliCommand and checkCommandInput(cliCommand,False):
            print("Delete directory functionality")

        elif "crdir" in cliCommand and checkCommandInput(cliCommand,False):
            print("Create directory functionality")

        elif "goindir" in cliCommand and checkCommandInput(cliCommand,False):
            print("Go inside a directory functionality")

        elif "lscurr" in cliCommand:
            print("Goes back to the root directory and list all files in the root directory")

        elif "lsroot" in cliCommand:
            print("Goes back to the root directory and list all files in the root directory")

        elif "exit" in cliCommand:
            sys.exit()

        else:
            print("Invalid Command")


if __name__ == "__main__":
    main()






