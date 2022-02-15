
import socket

TCP_IP = '127.0.0.1'
TCP_PORT = 8890

print("Attempting to contact server at ",TCP_IP,":",TCP_PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((TCP_IP, TCP_PORT))
print ("Connection to Server Established")
username = input("enter username:")
message = input("> ")
s.send(message.encode())
modifiedMessage, serverAddress = s.recvfrom(2048)
print(modifiedMessage.decode())
s.close()
