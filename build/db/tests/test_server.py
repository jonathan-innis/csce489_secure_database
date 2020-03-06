from db.server import TCPHandler, socketserver
import socket
import threading
import pytest


class example_server(socketserver.TCPServer):
    #nothing here for now?
    allow_reuse_addresss = True


class Test_TCPHandler:
    """
    def setUp(self):
        self.server = example_server(("localhost", 4444), TCPHandler)
        self.client = socket.create_connection(("localhost", 4444))
        self.server.serve_forever()

    def tearDown(self):
        self.client.close()
        self.server.shutdown()
        self.server.server_close()
    """
    def test_data_communication(self):
        server = example_server(("localhost", 4444), TCPHandler)
        server.serve_forever()
        #server_thread = threading.Thread(target=server.serve_forever())
        #server_thread.start()
        client = socket.create_connection(("localhost", 4444))
        client.send('test')
        result = client.recv(1024)
        assert result == "Message recieved: test"
        client.close()
        server.shutdown()
        server.server_close()
