from socket import *
import json
import rsa
import Pyro4
from .. import constants

def writeToUserListFile(userId, hashedPassword):
        with open('user_list.json','r+') as file:
            #Loading data into dictionary
            user_data = json.load(file)
            
            #Example for how to use and store keys in JSON file
            # (pub,pvt) = rsa.newkeys(512)
            # pubStr = rsa.PublicKey.save_pkcs1(pub)
            # pubStr = pubStr.decode()
            # pvtStr = rsa.PrivateKey.save_pkcs1(pvt)
            # pvtStr = pvtStr.decode()
            # message = 'hello Bob!'.encode()
            # crypto = rsa.encrypt(message, rsa.PublicKey.load_pkcs1(pubStr))
            # message = rsa.decrypt(crypto, rsa.PrivateKey.load_pkcs1(pvtStr))
            # print(message.decode())

            (encKey, decKey) = rsa.newkeys(512)
            encKey = rsa.PublicKey.save_pkcs1(encKey)
            decKey = rsa.PrivateKey.save_pkcs1(decKey)

            user = {
                "id":userId,
                "pwd":hashedPassword,
                "pvt_key":encKey.decode(),
                "pub_key":decKey.decode()
            }
            user_data['usersList'].append(user)

            file.seek(0)
            # convert back to json.
            json.dump(user_data, file, indent = 4)


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
            port = constants.authServerPort) 


if __name__ == "__main__":
    main()