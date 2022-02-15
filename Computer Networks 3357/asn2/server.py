import socket
import select
import urllib
import signal


# CS3357 Assignment 2
# October 19 2021

HEADER_LENGTH = 10
IP = '127.0.0.1' #local host
PORT = 1284

#go ahead and make the socket using TCP
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


#reuse the address so we dont have to keep changing and this will allow us to reconnect
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#bind and listen
serverSocket.bind((IP, PORT))
serverSocket.listen()

# we must have a list of client sockets to keep track of
socketsList = [serverSocket]

#create clients dictionary
clients = {}

#handler to handle if the user enters ctrl-c
def handler(signum, frame):
    res = input("Ctrl-c was pressed. Do you really wish to exit the chat? (y/n) ")
    if res == 'y':
        #send message to clients that server is closed

        exit(1)
signal.signal(signal.SIGINT,handler)
#recieve messages

#handling receiving messages
def receiveMessage(clientSocket):
    try:
        #read message header
        messageHeader = clientSocket.recv(HEADER_LENGTH)
        #if we dont get any data or get a closed connection
        if not len(messageHeader):
            return False
        #set length to length of the decoded message thats coming in
        messageLength = int(messageHeader.decode().strip())
        #return however long the socket is
        return{"header": messageHeader, "data":clientSocket.recv(messageLength)}
    except:
        #invalid registration error here
        #print("ERROR 400: Invalid registration")
        return False
while True:

    #select.select reads sockets_list, writes into empty list [], sockets we might error in
    readSockets, x, exceptionSockets = select.select(socketsList, [], socketsList)
    #iterate through read socket list
    for notifSocket in readSockets:
        #if the connection type is where the server just connected so the notified socket is the server
        if notifSocket == serverSocket:
            # handle the new connection
            clientSocket, clientAddress = serverSocket.accept()

            user = receiveMessage(clientSocket)
            if user is False:
                continue

             #add client socket to list
            socketsList.append(clientSocket)
            #save client username
            clients[clientSocket] = user
            print('Accpeted new connections from {}:{}, username: {}'.format(*clientAddress, user['data'].decode()))

        else:
            #if notifsocket isnt server then its a message that needs to be read
            message = receiveMessage(notifSocket)
            # make sure message exists
            if message is False:
                print('(DISCONNECT CHAT/1.0) Closed connection from: {}'.format(clients[notifSocket]['data'].decode()))

               #take it out of the list
                socketsList.remove(notifSocket)
                del clients[notifSocket]
                continue
            user = clients[notifSocket]
            print('received message from user {}:{}'.format((user['data'].decode()), message['data'].decode()))

            #share message with everybody
            for clientSocket in clients:
                if clientSocket != notifSocket:
                    #send the user header and data along with message header and data
                    clientSocket.send(user['header'] + user['data'] + message['header'] + message['data'])
    #handle errors
    for notifSocket in exceptionSockets:
        if notifSocket == user['data']:
            print("ERROR 401: username already in use")
        print("ERROR 400: Invalid Registration")
        socketsList.remove(notifSocket)
        del clients[notifSocket]

