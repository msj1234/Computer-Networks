import socket

IP = '127.0.0.1'
PORT = 8890

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((IP, PORT))
s.listen(1)

conn, addr = s.accept()
print('Server Address: ', IP)
print('Client Address: ', addr)
print('Connection to Client is Established')
conn.close()
