from socket import *
import json
import rsa
import Pyro4
import sys
sys.path.append("..")
import constants
from cryptography.fernet import Fernet
import crypto

auth_serv_pvt_key =  "-----BEGIN RSA PRIVATE KEY-----\nMIIBPAIBAAJBAJeBmlbGDCb9kQb0MPpdrwrHh1XU7VQ5pLdihSdqJQCl2ludW775\nHZLc/Qgkf0ssP9NPahPV5qX47UyRCVZTJI8CAwEAAQJAEodgJ8Ka093o8a/FmakB\nclEKpR2gVM+j7GWZIUPi4XyxlsbHoOZobtVa9ED8CpgNfnxTVZWJRsCFCrow5MmR\noQIjAL0TgDyWFRD2Es9QUo2q/L1FrLw4gx/Vq0vQtR/fD0DrSNECHwDNIdTBCwsq\nfSLNDk5F4YzDOY2a4+xB+EEpUTeI718CIjGbqzq6Of7AQYEpVu+anENgw4iC30x7\n+DylHtCk6tCiqvECHgfQAgpYIVS871Zf9Rs0O+gziPEdPSJGEjVAopzUgQIjAJaU\nbHgteJDH+n2KcSKnesi+9Ksq+AAdplWU89KaaKZ1J8w=\n-----END RSA PRIVATE KEY-----\n"


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
            fernetKey = Fernet.generate_key()

            user = {
                "id":userId,
                "pwd":hashedPassword,
                "pvt_key":encKey.decode(),
                "pub_key":decKey.decode(),
                "fernetKey": str(fernetKey)
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
        print(type(cliMsg))
        cliMsg = crypto.rsaDecryption(json.dumps(cliMsg).encode(), auth_serv_pvt_key)
        print(cliMsg)
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