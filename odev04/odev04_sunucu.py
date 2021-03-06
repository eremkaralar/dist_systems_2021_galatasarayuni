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
                tmp_name = data_str.split(" ",1)
                self.app_name = tmp_name[1]
                if qname == 'APP':
                    result = df[df["App"]==self.app_name].values.tolist()
                    empty_check = bool(result)
                    if empty_check == False:
                        response = 'NOTFOUND'
                      
                    else:
                        nresult = result[0]   
                        final_result = ' :: '.join(str(e) for e in nresult)
                        #Response icin protokol guncellemesi
                        protocol.update(
                            {'APP '+ self.app_name : 'PROPS ' + final_result })
                   

                elif qname == 'SEARCH':
                    self.app_name = tmp_name[1]
                    self.app_name_with_parameters = tmp_name[1]
                    split_parameters = self.app_name_with_parameters.split("::")
                    closest_list = difflib.get_close_matches(split_parameters[0], df.App,n=5)
                    splitted_name = split_parameters[0]
                   
                    if len(split_parameters) > 1:
                        param_val_split = split_parameters[1].split(":")
                        #Price parametresi
                        if param_val_split[0] == 'P':
                            price_value = param_val_split[1]
            
                            filtered_result = []
                            result_name = ""
                            for x in [0, 1, 2]:
                                raw_result = df[df["App"]==closest_list[x]].values.tolist()
                                result_price = raw_result[0][6]
                                result_name = raw_result[0][0]

                                if price_value == '0':
                                    if result_price == 'Free':
                                        filtered_result.append(result_name) 
                                else:
                                    if result_price == 'Free':
                                        num_res_price = 0
                                        if float(num_res_price) < float(price_value):
                                            filtered_result.append(raw_result[0][0]) 

                                filtered_str = unique_string(filtered_result)
                                protocol.update(
                                    {'SEARCH '+ self.app_name_with_parameters : 'APP FOUND ' + filtered_str })
           
                     #Rating-kategori icin parametre     
                    elif param_val_split[0] == 'R':
                        return 0       
                        
                    else:
                        #difflib kutuphanesi kullanarak en yakin 3 appi bulma
                        closest_list = difflib.get_close_matches(self.app_name, df.App,n=3)
                    #Bulunanlari uygun formata donusturerek protokolu guncelleme
                        closest_str = list_to_string(closest_list)
                        if not closest_str :
                            response = 'NOTFOUND'
                        else:
                            protocol.update(
                                {'SEARCH '+ self.app_name : 'APP FOUND ' + closest_str })
                        
                        

            #parametre error handling    
            if data_str in protocol.keys():
                response = protocol[data_str] + '\n'
            else:
                response = 'ERROR' + '\n' 

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
