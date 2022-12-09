# SecureP2P
Code : https://github.com/Saiteja-Peddi/SecureP2P

For Primary server:
Step 1: Change the pyrohost value in constants.py to your IP address found in your Wifi settings.
Step 2: In order to start name server the command is: python -m Pyro4.naming -n<your_host_name>
Step 3: Open new terminal and run authServer.py python file
Step 4: Open new terminal and run fileIndex.py python file
Step 5: Open new terminal and run peer.py python file
Step 6: Open new terminal and run client.py python file and perform file operations after authenticating yourself. You can create new credentials if you are a new user.

For Normal Peers:
Step 1: Change the pyrohost value in constants.py to your IP address found in your Wifi settings.
Step 2: Update the fileindex IP and authentication IP address in constants to which the primary server is located
Step 3: In order to start name server the command is: python -m Pyro4.naming -n<your_host_name> 
Step 4: Open new terminal and run peer.py python file
Step 6: Open new terminal and run client.py python file and perform file operations after authenticating yourself. You can create new credentials if you are a new user.


After login the options that can be displayed are
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
