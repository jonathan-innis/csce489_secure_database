#!/usr/bin/python

import json
import os
import subprocess
import sys
import tempfile
import time
import socket

# arguments
if len(sys.argv) != 3:
    print("usage: ./run-alt.py <server> <test>")
    exit(1)
serverFile = sys.argv[1]
testFile = sys.argv[2]

# helper functions
print("server file")
print(serverFile)
print("test file")
print(testFile)


def connect_to_server(port):
    s = socket.socket()         # Create a socket object
    s.connect(("localhost", port))
    return s


def send_input(s, inp):
    inp_bytes = str.encode(inp)
    s.send(inp_bytes)


def readlines(sock, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True
    while data:
        data = sock.recv(recv_buffer)
        buffer += data.decode('utf-8')
        # print(buffer)
        while buffer.find(delim) != -1:
            line, buffer = buffer.split('\n', 1)
            yield line
    return


def read_test():
    f = open(testFile, 'rb')
    test = json.loads(f.read())
    f.close()
    return test


def runServer(port):
    # print("about to do thing")
    p = subprocess.Popen(['npm', 'start', str(port)], shell=True)
    # print("did the thing")
    time.sleep(8)

    p.poll()
    # print("poll")
    # print( p.returncode)
    if p.returncode == 63:
        return runServer(port + 1)

    return (p, port)


def stopServer(p):
    p.terminate()
    p.wait()
    print("server exited with return code: " + str(p.returncode))

# go


# print("running tester thing")

spec = read_test()

# print("spec")

(p, port) = runServer(6320)

# print("ran server")

progs = spec['programs']
for proginfo in progs:
    # send program
    prog = proginfo['program']
    s = connect_to_server(port)
    # print("===> sending program ")
    # print(prog)
    send_input(s, prog)
    # get output
    # print("===> receiving output:")
    results = "["
    oneline = False
    for line in readlines(s):
        # print(line)
        if (oneline):
            results += ", "
        results += line
        oneline = True
    results += "]"
    s.close()
    res = json.loads(results)
    output = proginfo['output']
    if (res == output):
        print("===> output MATCHES")
    else:
        print("===> output DOES NOT match")

stopServer(p)
