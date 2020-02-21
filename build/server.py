#!/usr/bin/python3

import sys
import socketserver

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        self.request.sendall(b"Message recieved: " + self.data + b"\n")

if __name__ == "__main__":
    HOST, PORT = "localhost", int(sys.argv[1])
    if(len(sys.argv) == 3):
        password = sys.argv[2]  #here's the password to use when creating the admin principal
    else:
        password = "admin"

    server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
    server.serve_forever()