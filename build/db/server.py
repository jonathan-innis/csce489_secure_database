from parser.parser import Parser
import socketserver


class TCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, database, *args, **kwargs):
        self.__database = database
        super().__init__(*args, **kwargs)

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1000000).strip()  # limit of programs is 1 million chars - is this the correct way to measure that?
        parser = Parser()
        reply = parser.parse(self.__database, self.data.decode())
        # print("{} wrote:".format(self.client_address[0]))
        print(self.data.decode())
        print(reply)
        self.request.sendall(b"Message recieved: " + self.data + b"\n")
