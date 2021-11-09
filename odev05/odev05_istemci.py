import sys
import socket
import threading
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import queue
import time
from time import gmtime, strftime

#Gelen mesajlar ve tipleri icin class yaratimi
class gelenMsj:
    msj = ""
    nickname = ""
    tip = -1

    def __init__(self, org):
        self.org = org

class Enum(set):
    def __getattr__(self, tip):
        if tip in self:
            return tip
class mTip:
    yerTip = Enum(["LCL", "SERV"])
    cevapTip = Enum(["SYS", "LIST","NLOG", "NSIGN", "ERROR","REJ", "PUB", "PRIV"])

#App icin ayri thread olusacagindan screenQueue olarak duzenlendi
class ReadThread (threading.Thread):
    def __init__(self, name, csoc, threadQueue, screenQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.nickname = ""
        self.threadQueue = threadQueue
        self.screenQueue = screenQueue

    def incoming_parser(self, data):
        gelenmesaj = gelenMsj(mTip.yerTip.SERV)
        kmt = data[0:3]
        opw = data[4:]     
        print("Gelen data:", data.decode())     
        komut = kmt.decode()     
        if komut == "TIN":
            self.threadQueue.put("/tin")
            self.screenQueue.put(gelenmesaj)
            return
        if komut == "GNL":
            splittr = opw.split(":")
            gelenmesaj.tip = mTip.cevapTip.PUB
            gelenmesaj.nickname = splittr[0]
            gelenmesaj.msj = splittr[1]
            self.screenQueue.put(gelenmesaj)
            return "OKG"
        if komut == "PRV":
            splittr = opw.split(":")
            gelenmesaj.tip = mTip.cevapTip.PRIV
            gelenmesaj.nickname = splittr[0]
            gelenmesaj.msj = splittr[1]
            self.screenQueue.put(gelenmesaj)
            return "OKP"
        elif komut == "HEL":
            gelenmesaj.tip = mTip.cevapTip.NLOG
            gelenmesaj.nickname = opw  
            self.screenQueue.put(gelenmesaj)  
        elif komut == "WRN":
            gelenmesaj.tip = mTip.cevapTip.SYS
            gelenmesaj.msj = opw
            self.screenQueue.put(gelenmesaj)
        elif komut == "REJ":
            gelenmesaj.tip = mTip.cevapTip.REJ
            gelenmesaj.nickname = opw
            self.screenQueue.put(gelenmesaj)
        elif komut == "LST":
            gelenmesaj.type = mTip.cevapTip.LIST
            gelenmesaj.nickname = opw
            return "GLS"
        elif komut == "LRR":
            gelenmesaj.type = mTip.cevapTip.NSIGN
            self.screenQueue.put(gelenmesaj)
        elif komut == "ERR":
            gelenmesaj.type = mTip.cevapTip.ERROR
            self.screenQueue.put(gelenmesaj)

        return gelenmesaj
       
    def run(self):
        while True:
            data = self.csoc.recv(1024)
            msj = self.incoming_parser(data)
            if msj:
                self.screenQueue.put(msj)

class WriteThread (threading.Thread):
    def __init__(self, name, csoc, threadQueue,screenQueue):
        threading.Thread.__init__(self)
        self.name = name
        self.csoc = csoc
        self.threadQueue = threadQueue
        self.screenQueue = screenQueue

    def outgoing_parser(self, msj):
        if msj[0] == "/":
            splittr = msj.split(" ")
            kmt = splittr[0][1:]
          
            if kmt == "tin":
                return "TON"
            if kmt == "user":
                return "NIC " + splittr[1]
            if kmt == "list":
                return "GLS "
            if kmt == "quit":
                return "QUI "
            if kmt == "msg":
                return "MSG %s:%s" % (splittr[1], " ".join(splittr[2:]))
 
    def run(self):
        while True:
            if self.threadQueue.qsize() > 0:
                queueMsj = self.threadQueue.get()
                gidenMsj = self.outgoing_parser(queueMsj)
                if gidenMsj:
                    gidenMsj += "\n"
                    print("gidenMsj: " + gidenMsj)
                    try:
                        self.csoc.send(gidenMsj.encode())
                    except socket.error:
                        self.csoc.close()
                        break
                else:
                    gelenMesaj = gelenMsj(mTip.yerTip.LCL)
                    gelenMesaj.tip = mTip.cevapTip.SYS
                    gelenMesaj.msj = "Komut Hatası!"
                    self.screenQueue.put(gelenMesaj)

#App icin ayri thread olusacagindan screenQueue eklendi
class ClientDialog(QDialog):
    def __init__(self, threadQueue,screenQueue):
        self.threadQueue = threadQueue
        self.screenQueue = screenQueue
        self.qt_app = QApplication(sys.argv)
        QDialog.__init__(self, None)
        self.setWindowTitle('IRC Client')
        self.setMinimumSize(500, 200)
        self.vbox = QVBoxLayout()
        self.sender = QLineEdit("", self)
        self.channel = QTextBrowser()
        self.send_button = QPushButton('&Send')
        self.send_button.clicked.connect(self.outgoing_parser)
        self.vbox.addWidget(self.channel)
        self.vbox.addWidget(self.sender)
        self.vbox.addWidget(self.send_button)
        
# start timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateText)
        self.timer.start(10)
        self.setLayout(self.vbox)
    
    def updateText(self):
        if not self.screenQueue.empty():
            data = self.screenQueue.get()
            t = time.localtime()
            pt = "%02d:%02d:%02d" % (t.tm_hour, t.tm_min, t.tm_sec)
            msj = self.incoming_parser(data)
            if msj:
                msj = self.formatMessage(msj.decode(), False)
                self.channel.append(msj)            
        else: 
            return

    def cprint(self,data):
        self.channel.append(data)    

    def incoming_parser(self, msj):
        if isinstance(msj,str) == True:
            self.screenQueue.put(msj)
        else:    
            msjType = msj.tip
            cevapTip = mTip.cevapTip

            if msjType == cevapTip.PUB:
                return "<" + msj.nickname + ">:" + msj.msj
            if msjType == cevapTip.PRIV:
                return "*" + msj.nickname + "*:" + msj.msj
            elif msjType == cevapTip.LIST:
                userList = ""
                for item in msj.nickname.split(":"):
                    userList += item

                return userList   
            elif msjType == cevapTip.NLOG:
                screenQueue.put("Giris basarili: <" + msj.nickname + ">")
                return
            elif msjType == cevapTip.REJ:
                return "Kullanici reddi: <" + msj.nickname + ">"
            elif msjType == cevapTip.SYS:
                return msj.msj
            elif msjType == cevapTip.ERROR:
                return "Sunucu hatasi"
            elif msjType == cevapTip.NSIGN:
                return "Once giris yapin"
        
    def outgoing_parser(self):
        msj = str(self.sender.text())
        if len(msj) > 0:
            msjshow = self.formatMessage(msj, True)
            self.sender.clear()
            self.channel.append(msjshow)
            self.threadQueue.put(msj)
    
    def formatMessage(self, msj, isLocal):
        res = strftime("%H:%M:%S", gmtime())
        res +=  " -Local-" if isLocal else " -Server-"
        return res + ": " + msj
    
    def run(self):
        self.show()
        self.qt_app.exec_()

 # connect to the server
s = socket.socket()
host = str(sys.argv[1])
port = int(sys.argv[2])
s.connect((host,port))
sendQueue = queue.Queue(maxsize=0)          
screenQueue = queue.Queue(maxsize=0) 
app = ClientDialog(sendQueue,screenQueue)
# start threads
rt = ReadThread("ReadThread", s, sendQueue, screenQueue)
rt.start()
wt = WriteThread("WriteThread", s, sendQueue,screenQueue)
wt.start()
app.run()
rt.join()
wt.join()
s.close()