from db.server import TCPHandler, socketserver
import socket
import threading
import pytest


class example_server():
    # nothing here for now?
    allow_reuse_address = True

    def __init__(self, handler):
        # allow_reuse_address = True
        self.server = socketserver.TCPServer(('localhost', 0), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.__port = self.server.server_address[1]
        # self.server.serve_forever()

    def get_port(self):
        return self.__port

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


class Test_TCPHandler:

    def test_data_communication(self):
        server = example_server(TCPHandler)
        port = server.get_port()
        client = socket.create_connection(("localhost", port))
        client.send(b'test')
        result = client.recv(1024)
        assert result == b"Message recieved: test\n"
        client.close()
        server.stop()
