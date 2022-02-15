import socket
import select
import errno
import sys
import signal


# CS3357 Assignment 2
# October 19 2021

HEADER_LENGTH = 10
IP = "127.0.0.1" #the local host
PORT = 1284
#get username of client
client_username = input("Username: ")
#creating client socket using TCP
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#connect to ip and port
clientSocket.connect((IP, PORT))
# make sure receive function wont be blocking by setting it to false
clientSocket.setblocking(False)

# begin to send in info to server (send username to server)
username = client_username.encode()
usernameHeader = f"{len(username):<{HEADER_LENGTH}}".encode()
#send to the server
clientSocket.send(usernameHeader + username)

#handler to handle if the user enters ctrl-c
def handler(signum, frame):
    print("Ctrl-c was pressed. succefully left chat.")
    exit(1)
signal.signal(signal.SIGINT,handler)


#iterate in a loop to send messages and recieve messages
while True:
    message = input(f"{client_username} > ")
    #accont for if user enters space or is empty
    if message:
        #encode the message
        message = message.encode()
        #make a header and encode it
        messageHeader = f"{len(message):<{HEADER_LENGTH}}".encode()
       #send in the message
        clientSocket.send(messageHeader+message)

   #receive messages but account for errors
    try:

        while True:
            #prepare to grab header contents for receiving messages
            usernameHeader = clientSocket.recv(HEADER_LENGTH)
            #if we dont get any data,exit
            if not len(usernameHeader):
                print("DISCONNECT CHAT/1.0: Connection has been closed by the server.")
                sys.exit()
            #get the username
            usernameLength = int(usernameHeader.decode().strip())
            username = clientSocket.recv(usernameLength).decode()

            #get the message
            messageHeader = clientSocket.recv(HEADER_LENGTH)
            messageLength = int(messageHeader.decode().strip())
            #grab actual message itself
            message = clientSocket.recv(messageLength).decode()

            #then outprint to the screen
            print(f"{username} > {message}")
    #error handling
    except IOError as e:
        #errors we might see when there are no more messages to see
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print('ERROR 400: invalid registration', str(e))
            sys.exit()
        continue

    except Exception as e:
        print('ERROR', str(e))
        sys.exit()


