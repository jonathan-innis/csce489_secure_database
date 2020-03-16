from handler import *
from db.database import Database
from parser.parser import Parser
from functools import partial
import socket
import threading
import pytest
import time

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
        database = Database("admin")
        server = socketserver.TCPServer
        parser = Parser()
        handler = partial(TCPHandler, database, parser, server)
        server = example_server(handler)
        port = server.get_port()
        client = socket.create_connection(("localhost", port))
        client.send(b'test***')
        result = client.recv(1024)
        assert result == b"{'status': 'FAILED'}\n"
        client.close()
        server.stop()
        
    def test_create_principal(self):
        database = Database("admin")
        server = socketserver.TCPServer
        parser = Parser()
        handler = partial(TCPHandler, database, parser, server)
        server = example_server(handler)
        port = server.get_port()
        client = socket.create_connection(("localhost", port))
        client.send(b'as principal admin password "admin" do\n')
        client.send(b'   create principal alice "alices_password"\n')
        client.send(b'   return "success"\n')
        client.send(b'***')
        result = client.recv(1024)
        assert result == b"{'status': 'CREATE_PRINCIPAL'}\n{'status': 'RETURNING', 'output': 'success'}\n"
        client.close()
        server.stop()

    def test_create_principal_and_set_msg(self):
        database = Database("admin")
        server = socketserver.TCPServer
        parser = Parser()
        handler = partial(TCPHandler, database, parser, server)
        server = example_server(handler)
        port = server.get_port()
        client = socket.create_connection(("localhost", port))
        client.send(b'as principal admin password "admin" do\n')
        client.send(b'   create principal alice "alices_password"\n')
        client.send(b'   set msg = "Hi Alice. Good luck in Build-it, Break-it, Fix-it!"\n')
        client.send(b'   return "success"\n')
        client.send(b'***')
        result = client.recv(1024)
        assert result == b"{'status': 'CREATE_PRINCIPAL'}\n{'status': 'SET'}\n{'status': 'RETURNING', 'output': 'success'}\n"
        client.close()
        server.stop()

    def test_timeout(self):
        database = Database("admin")
        server = socketserver.TCPServer
        parser = Parser()
        handler = partial(TCPHandler, database, parser, server)
        server = example_server(handler)
        port = server.get_port()
        client = socket.create_connection(("localhost", port))
        time.sleep(30)
        result = client.recv(1024)
        assert result == b'{"status":"TIMEOUT"}\n'
        client.close()
        server.stop()
