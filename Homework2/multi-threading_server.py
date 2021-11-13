import socket
import threading
from _thread import *
from sumapi.api import SumAPI
import json

api_conn = SumAPI(username='GSUINF443', password='wHxuqxdQ95cT')
print_lock = threading.Lock()

def threaded(c):
	while True:
		data = c.recv(1024).decode()
		if not data:
			print('BYE BYE')
			print_lock.release()
			break

		to_sent_analysis = api_conn.sentiment_analysis(data, domain='general')
		c.send(bytes(json.dumps(to_sent_analysis), 'utf-8'))

	c.close()

def Main():
	host = ""
	port = 12345
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host, port))
	print("socket binded to port", port)
	s.listen(5)
	print("socket is listening")
	while True:
		c, addr = s.accept()
		print_lock.acquire()
		print('Connected to :', addr[0], ':', addr[1])
		start_new_thread(threaded, (c,))

	s.close()


if __name__ == '__main__':
	Main()
