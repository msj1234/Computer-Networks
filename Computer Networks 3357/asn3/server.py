import socket
import os
import signal
import sys
import selectors

# CS3357 Assignment 3
# November 9 2021

# Selector for helping us select incoming data and connections from multiple sources.

sel = selectors.DefaultSelector()

# Client list for mapping connected clients to their connections.
BUFFER_SIZE = 1024
client_list = []
follow_list = []


def check_dupe(list):
    if len(list) == len(set(list)):
        return False
    else:
        return True

# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message='DISCONNECT CHAT/1.0\n'
    for reg in client_list:
        reg[1].send(message.encode())
    sys.exit(0)

# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Search the client list for a particular user.

def client_search(user):
    for reg in client_list:
        if reg[0] == user:
            return reg[1]
    return None

# Search the client list for a particular user by their socket.

def client_search_by_socket(sock):
    for reg in client_list:
        if reg[1] == sock:
            return reg[0]
    return None

# Add a user to the client list.

def client_add(user, conn):
    registration = (user, conn)
    client_list.append(registration)


# Remove a client when disconnected.

def client_remove(user):
    for reg in client_list:
        if reg[0] == user:
            client_list.remove(reg)
            break



#sending a file to a client
def send_file_to_client(sock, file_name):
    #determine file type
    if(file_name.endswith('.gif')):
        type = 'image/gif'
    elif(file_name.endswith('.jpg')) or (file_name.endswith('.jpeg')):
        type =  'image/jpeg'
    elif(file_name.endswith('.png')):
        type = 'image/png'
    elif (file_name.endswith('.txt')):
        type = 'text'
    elif(file_name.endswith('.html')) or (file_name.endswith('.htm')):
        type = 'text/html'
    else:
        type = 'application/octet-stream'

    #get size of file
    file_size = os.path.getsize(file_name)

    #make a header and send it
    header = 'Content-Type: ' + type + '\r\nContent-Length: ' + str(file_size) + '\r\n\r\n'
    sock.send(header.encode())

    #open the file
    with open(file_name,'rb') as file_to_send:
        while True:
            part = file_to_send.read(BUFFER_SIZE)
            if part:
                sock.send(part)
            else:
                break



# Function to read messages from clients.

def read_message(sock, mask):
    global reg
    message = get_line_from_socket(sock)

    # Does this indicate a closed connection?

    if message == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()

    # Receive the message.

    else:
        user = client_search_by_socket(sock)
        print(f'Received message from user {user}:  ' + message)
        words = message.split(' ')

        command = message.split(' ')
        user_list = []


        if (words[1].startswith('!')):
            if(command[1] == '!list'):
                for user in client_list:
                    user_list.append(user[0])

                seperator = ", "
                msg = seperator.join(map(str,user_list))

                #send enocded message to client
                sock.send((msg + "\n").encode())


            #if the user enters !follow? list will be displayed
            elif ( "!follow?" in command):
                follow_list.append("@all")
                res = check_dupe(follow_list)
                #get list and print it as string
                for user in client_list:
                    #add if statemet to check if its alreayd in follow list
                    if res:
                        pass
                    else:
                        follow_list.append("@" + user[0])
                #prints the list of followers
                seperator = ", "
                msg = seperator.join(map(str, follow_list))

                #send to client
                sock.send(("Follow list: " + msg + "\n").encode())

            #removes item from following list
            elif(command[1] == '!unfollow'):
                res = check_dupe(follow_list)
                for user in client_list:
                    if res:
                        pass
                    else:
                         follow_list.append("@" + user[0])
                seperator = ", "
                msg = seperator.join(map(str, follow_list))
                print("Followed items: " + f'{msg}')

                topics = message.split()


                #if they try to remove @all or themselves send error
                if(topics[2] == "@all" or topics[2] == sock):
                    sock.send(("Error cannot remove topic \n").encode())

                #remove followed item from list and if doesnt exist outputs error
                else:
                    try:
                        follow_list.remove(topics[2]) #remove it from follow list
                       # msg = 'Unfollowing: ' + topics[2]
                        sock.send(("successfully unfollowed.\n").encode())
                    except:
                        sock.send(("Error the topic is not in follow list \n").encode())

                    print("Follow list: " + f'{msg}')


           #adds items to follow list
            elif (command[1] == '!follow'):

                #get list and pritn as string
                for user in client_list:
                    follow_list.append("@" + user[0])
                seperator = ", "
                msg = seperator.join(map(str, follow_list))

                topics = message.split()

                if topics[2] in follow_list:
                    #send error message to client
                    sock.send(("Error: Topic already exists in follow list.\n").encode())
                else:
                    #else add to follow list
                    follow_list.append(topics[2])
                    #send back to client
                    sock.send(("Now Following: " + topics[2] + "\n").encode())
                print("Followed items: " + f'{msg}')


            #exit user from chat
            elif (command[1] == '!exit'):

                #disconnect them from the server
                print('Disconnecting user ' + user)
                response='DISCONNECT CHAT/1.0\n'
                sock.send(response.encode())
                client_remove(user)
                sel.unregister(sock)
                sock.close()


            #attaching a file
            #recieve file from Client A
            # send the file to Client B
            elif (command[1] == '!attach'):
                #retrieve and write the file out
                try:

                    #gets size of file
                    parts = message.split()

                    file_name = parts[2]
                    print ("Name of file: " + file_name)
                    global thisFile
                    thisFile = file_name

                    #check if file exists
                    if not os.path.exists(file_name):
                        msg = 'requested file doesnt exist\n'
                        sock.send(msg.encode())
                    else:
                        #send file
                        msg = 'sending file...\n'
                        sock.send(msg.encode())
                        send_file_to_client(sock,file_name)

                #exception if there is an error in reading the file
                except Exception as e:
                    print(e)


            else:
                msg = 'invalid command\n'
                sock.send(msg.encode())


        # Check for client disconnections.

        if words[0] == 'DISCONNECT':
            print('Disconnecting user ' + user)
            client_remove(user)
            sel.unregister(sock)
            sock.close()
        elif words[0] == '!list':
            print("Worked wih word array")

        # Send message to all users.  Send at most only once, and don't send to yourself.
        # Need to re-add stripped newlines here.

        else:
            for reg in client_list:
                if reg[0] == user:
                    continue
                client_sock = reg[1]
                forwarded_message = f'{message}\n'
                client_sock.send(forwarded_message.encode())



# Function to accept and set up clients.

def accept_client(sock, mask):
    conn, addr = sock.accept()
    print('Accepted connection from client address:', addr)
    message = get_line_from_socket(conn)
    message_parts = message.split()

    # Check format of request.

    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0')):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')
        response='400 Invalid registration\n'
        conn.send(response.encode())
        conn.close()

    # If request is properly formatted and user not already listed, go ahead with registration.

    else:
        user = message_parts[1]

        if (client_search(user) == None):
            client_add(user,conn)
            print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')
            response='200 Registration succesful\n'
            conn.send(response.encode())
            conn.setblocking(True)
            sel.register(conn, selectors.EVENT_READ, read_message)

        # If user already in list, return a registration error.

        else:
            print('Error:  Client already registered.')
            print('Connection closing ...')
            response='401 Client already registered\n'
            conn.send(response.encode())
            conn.close()


# Our main function.

def main():

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(100)

    server_socket.setblocking(True)
    sel.register(server_socket, selectors.EVENT_READ, accept_client)
    print('Waiting for incoming client connections ...')

    # Keep the server running forever, waiting for connections or messages.

    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

if __name__ == '__main__':
    main()

