from parser.parser import Parser
import socketserver
import json


class TCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, database, *args, **kwargs):
        self.__database = database
        super().__init__(*args, **kwargs)

    def handle(self):
        # http://code.activestate.com/recipes/408859/
        End = '***'
        total_data = []
        data = ''
        while True:
            data = self.request.recv(8192)
            data = data.decode()
            if End in data:
                total_data.append(data)
                break
            total_data.append(data)
        result = ''.join(total_data)
        parser = Parser()
        reply = parser.parse(self.__database, result.strip())
        json_reply = json.dumps(reply)
        self.request.sendall(json_reply.encode('utf-8') + b"\n")

