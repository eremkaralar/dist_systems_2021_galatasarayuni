from enum import unique
import socket 
import threading
import queue
import time
import pandas
import difflib


#Dosyayi bulundugu yerden okuma
df = pandas.read_csv(r'/Users/eremkaralar/Desktop/GooglePlayData/googleplaystore.csv')


def list_to_string(list):
    
    tostring = ''
    for x in list:
        
        tostring = tostring + ' :: ' + x

    return tostring



# Kategori listesini biriciklestirme ve protokol icinde gosterebilmek icin yazilmis fonksiyon
def unique_string(list1):
 
    unique_list = []
    unique_string = ""

    for x in list1:
     
        if x not in unique_list:
            unique_list.append(x)
            unique_string = unique_string + ' :: ' + x

    return unique_string    


#Spesifik kolonu okuma ardindan biriciklestirme
list = df.Category
ulist = unique_string(list)

protocol = {'HELLO' : 'HELLO :: EREM',
            'LIST':'CATEGORIES' + ulist,
            'QUIT' : 'BYE BYE'
}


#thread
class myThread (threading.Thread):
    def __init__(self, threadID, cSocket, addr):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.client_socket = cSocket
        self.address = addr
        
    def run(self):
        print ("Starting: ",self.threadID)
        saat = time.ctime()
        self.client_socket.send((saat + "\n").encode())
        while True:
            data = self.client_socket.recv(1024)
            data_str = data.decode().strip()
            tmp_query = data_str.split(" ",1)
            qname = tmp_query[0]

            if (qname == 'APP') or (qname == 'SEARCH'):
                print("innnn")
                tmp_name = data_str.split(" ",1)
                self.app_name = tmp_name[1]
                if qname == 'APP':
                #NOTFOUND - Key-Value Protokole eklenmedigi icin direkt NOTFOUND verecek.
                    if df[df["App"]==self.app_name].empty == False :
                        result = df[df["App"]==self.app_name].values.tolist()
                        #List icinde list halindeki satiri string haline donusturme islemleri
                        nresult = result[0]
                        final_result = ' :: '.join(str(e) for e in nresult)
                        #Response icin protokol guncellemesi
                        protocol.update(
                            {'APP '+ self.app_name : 'PROPS ' + final_result })
                elif qname == 'SEARCH':
                    self.app_name = tmp_name[1]
                    #difflib kutuphanesi kullanarak en yakin 3 appi bulma
                    closest_list = difflib.get_close_matches(self.app_name, df.App,n=3)
                    #Bulunanlari uygun formata donusturerek protokolu guncelleme
                    closest_str = list_to_string(closest_list)
                    protocol.update(
                            {'SEARCH '+ self.app_name : 'APP FOUND ' + closest_str })

                
            if data_str in protocol.keys():
                response = protocol[data_str] + '\n'
            else:
                response = 'NOTFOUND' + '\n' 

            self.client_socket.send(response.encode())

            if data_str == 'QUIT':
                client_socket.close()
                break
            


        print("Ending: ",self.threadID)

server_socket = socket.socket()
host = "0.0.0.0"
port = 12345
server_socket.bind((host, port))
server_socket.listen(1)   
    
thread_counter = 0

while True:
    print("New connection is waited. ")
    client_socket, addr = server_socket.accept()
    print("Yeni baglanti geldi:", addr)

    th = myThread(thread_counter, client_socket, addr)
    thread_counter += 1
    th.start()  
