#!/usr/bin/python3


import socket as s
import json
import subprocess
import sys
import time

oracle = './oracle'

# yes, this is needlessly recursive
def start_oracle(port):
	while True:
		po = subprocess.Popen([oracle, str(port)])
		time.sleep(1)
		po.poll()
		e = po.returncode
		if e is None:
			return po, port
		else:
			if e == 63:
				port += 1
			else:
				print("Server shutdown: ", e)
				exit(1)
	raise Exception("Failed to start oracle")

def kill_oracle(p):
	p.terminate()
	p.wait()

def main(test):
	port = 5000
	f = open(test, 'r')
	if f is None:
		print("{} can not be opened".format(test))
		exit(2)
	tests =  json.loads(f.read())
	f.close()
	programs = tests['programs']
	p, port = start_oracle(5000)
	try:
		if p is None:
			print("Error starting oracle")
			exit(1)
		for test in programs:
			program = test['program']
			c = s.socket()
			c.connect(('localhost', port))
			c.send(program.encode('utf-8'))
			output = ""
			while True:
				d = c.recv(4096)
				if not d:
					break
				output += d.decode('utf-8')
			print(output)
	except Exception as e:
		print(e)
		kill_oracle(p)
	else:
		kill_oracle(p)
	
if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('usage: {} <json/file>'.format(sys.argv[0]))
		exit(1)

	test = sys.argv[1]
	main(test)


