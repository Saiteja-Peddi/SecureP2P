from cryptography.fernet import Fernet

# Encrypts the file data using fernet encryption method
def fernetEncryption(encryptingText, key):
    # key = key.lstrip("\"")
    # key = key.rstrip("\"")
    f = Fernet(key)
    response = f.encrypt(bytes(encryptingText, encoding='utf8'))
    response = str(response)
    response = response.lstrip("b'")
    response = response.rstrip("'")
    return str(response)

# Decrypts the file data using fernet encryption method
def fernetDecryption(decryptingText, key):
    f = Fernet(key)
    response = f.decrypt(bytes(decryptingText, encoding='utf8'))
    return response.decode()

# Encrypts the file name
def fileNameEncryption(data, shift):
    
    shift = int(shift)
    i = len(data) - 1
    reversed = data[::-1]
    output = ""
    for i in range(len(reversed)):
        char = reversed[i]
        if char.isupper():
            output += chr((ord(char) + shift-65) % 26 + 65)
        elif char.islower():
            output += chr((ord(char) + shift - 97) % 26 + 97)
        elif char == "/":
            output += "dskedwaf#emfkww*fsfwref"
        else:
            output += char
 
    return output

# Decrypts the file name
def fileNameDecryption(data, shift):
    shift = int(shift)
    decShift = 26 - shift
    output = ""
    data = data.replace("dskedwaf#emfkww*fsfwref","/")
    for i in range(len(data)):
        char = data[i]
        if (char.isupper()):
            output += chr((ord(char) + decShift-65) % 26 + 65)
        elif(char.islower()):
            output += chr((ord(char) + decShift - 97) % 26 + 97)
        else:
            output += char

    reversed = output[::-1]
    return reversed
