import json
import time
import os
import Pyro4
import constants
import crypto

nameserver=Pyro4.locateNS(host = constants.fileIndexHost)
fileIndexUri = nameserver.lookup("example.fileIndex")
fileIndexServer = Pyro4.Proxy(fileIndexUri)

def callPeer(peer,clientRequest, printResponse = True):
    clientRequest = crypto.fernetEncryption(clientRequest, constants.peerCommEncKey)
    peerName,nsIP = peer.split(",")
    nsIP = nsIP.strip("\n")
    nameserver=Pyro4.locateNS(host = nsIP)
    peerUri = nameserver.lookup(peerName)
    peerObj = Pyro4.Proxy(peerUri)
    serverResponse = peerObj.fileRequestHandler(clientRequest)
    serverResponse = crypto.fernetDecryption(serverResponse, constants.peerCommEncKey)
    if printResponse:
        print("\n----------------------------------------")
        print("Server response:\n")
        print(serverResponse.split("|")[1])
        print("----------------------------------------")
    if serverResponse.split("|")[0] == "1":
        return True
    else:
        return False


def deleteScheduler():
    clientRequest = "PERMANENT_DELETE"
    peerList = fileIndexServer.getAllPeers()
    peerList = crypto.fernetDecryption(peerList, constants.peerCommEncKey)
    if not peerList == "":
        for i, peer in enumerate(peerList.split("|")):
            callPeer(peer,clientRequest,False)
        response = fileIndexServer.permanentDelete()
        response = crypto.fernetDecryption(response, constants.peerCommEncKey)
        print(response.split("|")[1])


def main():
    print("Scheduler running")
    while True:
        deleteScheduler()
        time.sleep(10)

if __name__ == "__main__":
    main()