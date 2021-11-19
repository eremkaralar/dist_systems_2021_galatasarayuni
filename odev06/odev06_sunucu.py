#/usr/bin/env python3
from os import write
import socket
import threading
import time
import queue

class write_thread(threading.Thread):
    def __init__(self, name, cSock,cAddr,cQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.cSock = cSock
        self.cAddr = cAddr
        self.cQueue = cQueue

    def run(self):
        print(self.name , "starting...")
        self.cSock.send(b'Welcome')

        while True:
            data = self.cQueue.get()
            self.cSock.send(data.encode())
        

            if data == "BYE":
                time.sleep(1)
                self.cSock.close()
                break

        print(self.name, "ending...")    

class read_thread(threading.Thread):
    def __init__(self, name, cSock,cAddr,cQueue,fihrist):
        threading.Thread.__init__(self)
        self.name = name
        self.cSock = cSock
        self.cAddr = cAddr
        self.cQueue = cQueue
        self.fihrist = fihrist
        self.username = None

    def run(self):
        print(self.name , "starting...")
        #self.cSock.send(b'Welcome')
        while True:  
            data = self.cSock.recv(1024).decode().strip()
            retVal = self.incoming_parser(data)
        
            if retVal == 1:
                break
            
            #print(self.cAddr, "says: ", data.decode())
            #self.cSock.send(b'OK')


        print(self.name , "ending...")

    def incoming_parser(self,data):
        ret = 0
        if data[:4] == "NIC ":
            username = data[4:]
            if len(username) > 0:
                if username in self.fihrist.keys():
                    response = "REJ" + username
                else:
                    response = "WEL" + username   
                    self.username = username
                    self.fihrist[username] = self.cQueue

        elif data[:4] == "PRV":
            if self.username == None:
                response = "LRR"
            #error handling
            else:
                split_data = data[:4].split(":",1)
                if len(split_data) == 2:
                    target_user = split_data[0]
                    message = split_data[1]
                    if target_user in self.fihrist.keys():
                        response = "OKP"
                        
                        self.fihrist[target_user].put("PRV " + self.username + ":" + message)

                    else:
                        response = "NOP"
                
                else:
                    response = "ERR"


        elif data == "PIN":
            response = "PON"

        elif data == "QUI":
            response = "BYE"
            ret = 1

        else:
            response = "ERR"    
                       
        self.cQueue.put(response)


        return ret



def main():
    port = 12345
    host = "0.0.0.0"
    thread_count = 0

    l_sock = socket.socket()
    l_sock.bind((host,port))

#Herkese cevap vermek icin buffera gerek yok o yuzden param 0
    l_sock.listen(0)

    fihrist = ()
    print("Server is commencing! ")
    
    while True:
        c_sock,c_addr = l_sock.accept()
        q = queue.Queue()
        writeThread = write_thread("Write Thread - " + str(thread_count),c_sock,c_addr,q)
        print("Client has connected:  "
        ,c_addr)
        readThread = read_thread("Read thread - " + str(thread_count),c_sock,c_addr,q)
        #run()
        readThread.start()
        writeThread.start()
        thread_count += 1
    print("Server is terminating ")


    
if __name__ == "__main__":
    main()