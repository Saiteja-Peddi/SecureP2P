from socket import *
import json
import Pyro4
import sys
sys.path.append("..")
import constants
from cryptography.fernet import Fernet
import crypto


def writeToUserListFile(userId, hashedPassword):
        with open('user_list.json','r+') as file:
            #Loading data into dictionary
            user_data = json.load(file)
            fernetKey = str(Fernet.generate_key().decode())
            fernetKey = fernetKey.lstrip("b'")
            fernetKey = fernetKey.rstrip("'")
            user = {
                "id":userId,
                "pwd":hashedPassword,
                "fernetKey": fernetKey
            }
            user_data['usersList'].append(user)

            file.seek(0)
            # convert back to json.
            json.dump(user_data, file, indent = 4)
            file.close()


def verifyUserId(userId, usersList):
        #Returns True if user exist or else False
        if len(usersList) == 0:
            return -1
        else:
            for ind, usr in enumerate(usersList):
                if usr['id'] == userId:
                    return ind
            
            return -1
def createUser(userId, hashedPassword):
        userListFile = open('user_list.json')
        users = json.load(userListFile)
        usersList = users['usersList']
        flag = verifyUserId(userId, usersList)
        if flag == -1:
            writeToUserListFile(userId, hashedPassword)
            return "1|User created successfully"

        else:
            return "0|Unable to create user"
                
def loginUser(userId, hashedPassword):
    userListFile = open('user_list.json')
    users = json.load(userListFile)
    usersList = users['usersList']
    ind = verifyUserId(userId, usersList)
    if ind != -1:
        user = usersList[ind]
        if user['pwd'] == hashedPassword:
            return "1|Login Successful"
        else:
            return "0|Invalid credentials"
    else:
        return "0|Invalid credentials"



@Pyro4.expose
class AuthServer(object):

    def __init__(self):
        pass

    def authRequestHandler(self, cliMsg):
        cliMsg = crypto.fernetDecryption(cliMsg,constants.authServerEncKey)
        if "CREATE_USER" in cliMsg:
            userId,hashedPassword = cliMsg.split("|")[1:]
            message = createUser(userId, hashedPassword)
        
        elif "LOGIN_USER" in cliMsg:
            userId,hashedPassword = cliMsg.split("|")[1:]
            message = loginUser(userId,hashedPassword)

        else:
            message = "0|Invalid option selected"
        
        return message


def main():
    Pyro4.Daemon.serveSimple(
            {
                AuthServer: "example.authServer"
            },
            ns = True,
            host = constants.pyroHost,
            port = constants.authServerPort
    )


if __name__ == "__main__":
    main()