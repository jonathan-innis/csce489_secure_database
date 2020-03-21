from handler import *
from db.database import Database
from parser.parser import Parser
from functools import partial
import socket
import threading
import pytest
import time
import json


def validate_tests(d, tests):
    server = StoppableServer
    parser = Parser()
    handler = partial(TCPHandler, d, parser, server)
    server = example_server(handler)
    port = server.get_port()
    client = socket.create_connection(("localhost", port))
    for test in tests:
        lines = test["text"].splitlines(True)
        print(lines)
        for line in lines:
            client.send(bytes(line, 'utf-8'))
        result = client.recv(1024)
        ret = [json.loads(elem) for elem in str(result.decode('utf-8')).splitlines()]
        assert len(ret) == len(test["exp_status"])
        for i, code in enumerate(ret):
            assert code["status"] == test["exp_status"][i]
        if "output" in test:
            if isinstance(test["output"], list):
                for first, second in zip(test["output"], ret[-1]["output"]):
                    if isinstance(first, dict):
                        for k in first:
                            assert k in second
                            assert first[k] == second[k]
                    else:
                        assert first == second
            elif isinstance(test["output"], dict):
                for k in ret[-1]["output"]:
                    assert k in test["output"]
                    assert ret[-1]["output"][k] == test["output"][k] 
            assert ret[-1]["output"] == test["output"]
        else:
            assert "output" not in ret[-1]
    client.close()
    server.stop()


class example_server():
    # nothing here for now?
    allow_reuse_address = True

    def __init__(self, handler):
        # allow_reuse_address = True
        self.server = StoppableServer(('localhost', 0), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()
        self.__port = self.server.server_address[1]
        # self.server.serve_forever()

    def get_port(self):
        return self.__port

    def stop(self):
        self.server._BaseServer__shutdown_request = True


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
        print(result)
        assert result == b'{"status": "FAILED"}\n'
        client.close()
        server.stop()
        
    def test_create_principal(self):
        tests = [
            {
                "text": 'as principal admin password "admin" do\n   create principal alice "alices_password"\n  return "success"\n***',
                "exp_status": ["CREATE_PRINCIPAL", "RETURNING"],
                "output": "success"
            }
        ]
        database = Database("admin")
        validate_tests(database, tests)

    def test_create_principal_and_set_msg(self):
        tests = [
            {
                "text": 'as principal admin password "admin" do\n   create principal alice "alices_password"\n    set msg = "Hi Alice. Good luck in Build-it, Break-it, Fix-it!"\n    return "success"\n***',
                "exp_status": ["CREATE_PRINCIPAL", "SET", "RETURNING"],
                "output": "success"
            }
        ]
        database = Database("admin")
        validate_tests(database, tests)

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
        assert result == b'{"status": "TIMEOUT"}\n'
        tests = [
            {
                "text": 'as principal admin password "admin" do\nexit\n***',
                "exp_status": ["EXITING"],
            }
        ]
        validate_tests(database, tests)
        client.close()
        server.stop()
