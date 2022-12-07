# SecureP2P

The popularity of  file systems continues to grow. Fault tolerance, availability, scalability, and performance make them preferable to conventional centralized file systems. We are using the python programming language to create a secure and encrypted  P2P file system. For redundancy of the files and directories that are saved, we use a main file server and two replica servers. This file system enables us to share files with multiple users while ensuring that all operations are secure and performed by authorized users. 

As like all file systems, our system too has a basic set of Input Output functionalities. Files can be created, deleted, read, written, and restored by authorized users. Concurrent users can also perform operations on the DFS while the ACID (Atomicity, Consistency, Isolation, and Durability) properties are maintained.The use of Fernet to encrypt and decrypt data between users is being discussed as a means of ensuring security and secrecy to avoid unauthorized users from accessing data. 

<b>Design</b>

An important and clearly described encrypted file system created in the Python programming language was demonstrated in this project. The system is designed to include all of a  file system's fundamental features. The system is made more secure with the addition of encryption, directory-based features, and login-based features.

The flow chart figure-1 below explains the flow of file system’s authentication. As the user has to provide valid credentials to access the system. Once the user raises the request, the data packets in encrypted form will reach the server to verify in the File Index server and as all are authenticated, users will receive the access token and continue with their file operations.If the user is a new one, one can create an account with username and password. As these credentials will be stored in the server. As the Authentication server provides access to the Index server and peers after authenticating the client. Clients can request file operation[Read, Write, Delete and Restore] to index server. Client can create a specific file request to the respective peer.Index server then provides a link to the respective peer in which it contains the requested file. 
Note : Below we have referenced the requesting peer as client. So, wherever you see a client it simply means a peer. 

<b>Encryption</b>

1.All communications between the peers and Index servers use Fernet encryption algorithm 
2.For encrypting the content within the file and file name we are writing our own encryption function.



