#/usr/bin/env python3
from os import write
import socket
import threading
import time
import queue

class Write_Thread(threading.Thread):
    def __init__(self, name, client_socket, client_address, client_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_queue = client_queue

    def run(self):
        print(f"{self.name} commencing..")
        self.client_socket.send(b'Welcome.\n> ')

        while True:
            response = self.client_queue.get()
            self.client_socket.send(self.format_message(response).encode())

            if (response == "BYE"):
                time.sleep(.2)
                self.client_socket.close()
                break

        print(f"{self.name} ending..")
    
    def format_message(self, data):
        return (data + "\n> ")


class Read_Thread(threading.Thread):
    def __init__(self, name, client_socket, client_address, client_queue, fihrist):
        threading.Thread.__init__(self)
        self.name = name
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_queue = client_queue
        self.fihrist = fihrist

    def run(self):
        print(f"{self.name} commencing..")
        
        while True:
            data = self.client_socket.recv(1024).decode().strip()        
            return_value = self.incoming_parser(data)

            if return_value == 1:
                break

        print(f"{self.name} ending..")

    def incoming_parser(self, data):
        ret = 0

        if (data[:4] == "NIC "):
            username = data[4:]
            if len(username) > 0:
                if (username in self.fihrist.keys()):
                    response = "REJ {username}"
                else:
                    response = "WEL {username}"
                    self.fihrist[username] = self.client_queue
                    self.username = username

        elif data[:4] == "PRV ":
            if (self.username == None):
                response = "LRR"
            else:
                splitted_data = data[4:].split(":")
                
                if (len(splitted_data) == 2):
                    target_user = splitted_data[0]
                    message = splitted_data[1]

                    if (target_user in self.fihrist.keys()):
                        response = "OKP"
                        self.fihrist[target_user].put(f"PRV {self.username}:{message}") 
                    else:
                        response = "NOP"
                else:
                    response = "ERR"
    
        elif (data == "PIN"):
            response = "PON"
        elif (data == "QUI"):
            response = "BYE"
            ret = 1
        else:
            response = "ERR"

        self.client_queue.put(response)
        
        return ret

def main():
    port = 12345
    host = "0.0.0.0"
    thread_counter = 0

    listener_socket = socket.socket()
    listener_socket.bind((host, port))

    listener_socket.listen(0)

    fihrist = {}

    print("Server is initializing..")
    while True:
        client_socket, client_address = listener_socket.accept()
        print("A new client has connected: ", client_address)

        message_queue = queue.Queue()

        write_thread = Write_Thread("WriteThread-" + str(thread_counter), client_socket, client_address, message_queue)
        read_thread = Read_Thread("ReadThread-" + str(thread_counter), client_socket, client_address, message_queue, fihrist)
        
        read_thread.start()
        write_thread.start()

        thread_counter += 1

    print("Server has closed.")

if __name__ == "__main__":
    main()