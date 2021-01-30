import socket                
import sys

# Create a socket object 
s = socket.socket()          
  
# Define the port on which you want to connect 
port = int(sys.argv[1])
# connect to the server on local computer 
s.connect(('127.0.0.1', port)) 

while True:
    userInput = input("")
    s.send(str.encode(userInput))
    if (userInput == "exit"):
        break
# close the connection 
s.close()
