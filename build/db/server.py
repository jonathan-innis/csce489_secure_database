from parser.parser import Parser
import socketserver
import socket


class TCPHandler(socketserver.BaseRequestHandler):
    def __init__(self, database, server, *args, **kwargs):
        self.__database = database
        self.__server = server
        self.__parser = Parser()
        super().__init__(*args, **kwargs)

    def handle(self):
        # http://code.activestate.com/recipes/408859/
        self.request.settimeout(30)
        try:
            END = '***'
            total_data = []
            data = ''
            while True:
                data = self.request.recv(8192)
                data = data.decode()
                if END in data:
                    total_data.append(data)
                    break
                total_data.append(data)
            result = ''.join(total_data)
            reply = self.__parser.parse(self.__database, result.strip())
            final_reply = '\n'.join([str(elem) for elem in reply])
            self.request.sendall(final_reply.encode('utf-8') + b"\n")
            # https://stackoverflow.com/a/36017741
            if 'EXITING' in final_reply:
                self.server._BaseServer__shutdown_request = True
        except socket.timeout:
            self.request.sendall(b'{"status":"TIMEOUT"}' + b"\n")
