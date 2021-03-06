#/usr/bin/env python3
from os import write
import socket
import threading
import time
import queue
from time import gmtime, strftime
import os
import sys

class Logger_Thread(threading.Thread):
    def __init__(self, name, client_socket, client_address, client_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_queue = client_queue

    def run(self):
        print(f"{self.name} commencing..")
        logs = ""

        while True:
            #Log tutulmasi burada gerceklesir.
            response = self.client_queue.get()
            single_log = self.format_message(response)
            logs = logs + single_log
            with open(os.path.join(sys.path[0], "logs.txt"), "w+") as f:
                f.write(logs)

            if (response == "BYE"):
                time.sleep(.2)
                self.client_socket.close()
                break

        print(f"{self.name} ending..")
    
    def format_message(self, data):
        res = strftime("%H:%M:%S", gmtime())
        return (res + ": " + data + "\n> ")
        
 
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
    def __init__(self, name, client_socket, client_address, client_queue, fihrist,logger_queue):
        threading.Thread.__init__(self)
        self.name = name
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_queue = client_queue
        self.fihrist = fihrist
        self.logger_queue = logger_queue

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

        if (data[:4] == "REG "):
            splitted_data = data[4:].split(":")
            if len(splitted_data) == 2:
                uname = splitted_data[0]
                pword = splitted_data[1]
                user = {uname:pword}
                self.fihrist.update(user)
                response = "OKR " + (uname)
            else:
                response = "NOR" 

        elif (data[:4] == "NIC "):
            splitted_data = data[4:].split(":")
            uname = splitted_data[0]
            pword = splitted_data[1]
            if len(uname) > 0:
                if (uname not in self.fihrist.keys()):
                    response = "REJ " + (uname)
                else:
                    if ((uname,pword) not in self.fihrist.items()):
                        response = "WPW " + (uname)
                    else:    
                        response = "HEL " + (uname)
                        self.fihrist[uname] = self.client_queue
                        self.username = uname
        elif (data[:4] == "CHP "): 
            splitted_data = data[4:].split(":")
            uname = splitted_data[0]
            newpword = splitted_data[1]
            if len(splitted_data) == 2:
                if (uname not in self.fihrist.keys()):
                    response = "CRR "
                else:
                    self.fihrist.update({uname : newpword})
                    response = "OKC " + (uname)
            else:
                response = "CRR "       

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
        self.logger_queue.put(data)
        self.logger_queue.put(response)
        
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
        logger_queue = queue.Queue()

        write_thread = Write_Thread("WriteThread-" + str(thread_counter), client_socket, client_address, message_queue)
        read_thread = Read_Thread("ReadThread-" + str(thread_counter), client_socket, client_address, message_queue, fihrist,logger_queue)
        logger_thread = Logger_Thread("LoggerThread-" + str(thread_counter), client_socket, client_address, logger_queue)
        
        read_thread.start()
        write_thread.start()
        logger_thread.start()

        thread_counter += 1

    print("Server has closed.")

if __name__ == "__main__":
    main()