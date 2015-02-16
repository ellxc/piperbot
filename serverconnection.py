import socket
from queue import PriorityQueue
import threading
import re
from Message import Message
import time
from ssl import wrap_socket
import events





SPLIT_REGEX = r"^(?::(?:(?:(?P<nick>\S+)!)?(?:(?P<user>\S+)@)?(?P<domain>\S+) +))?" \
              r"(?P<command>\S+)(?: +(?!:)(?P<params>.+?))?(?: *:(?P<action>\x01ACTION )?(?P<text>.+?))?\x01?$"


def handler(self,event):
    def wrapper(func):
        self.handlers[event] = func
        return func
    return wrapper
  
              
class ServerConnection():
    def __init__(self, queue, name, network, port, nick, password=None, username=None, ircname = None, auto_join_channels=None,ssl=False):
        self.in_queue = queue
        self.out_queue = PriorityQueue()
        self.connected = False
        self.name = name
        self.network = network
        self.port = port
        self.ssl = ssl
        self.nick = nick
        self.user = username or nick
        self.ircname = ircname or nick
        self.password = password
        self.auto_join_channels = auto_join_channels if auto_join_channels else []

        self.handlers = dict()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl:
            self.socket = wrap_socket(self.socket)
        self.socket.bind(('', 0))
        self.in_thread = self.InThread(self)
        self.out_thread = self.OutThread(self.socket, self.out_queue, self.reconnect)

        
        @handler(self,"001")
        def on_connect(self):
            print("JOINED")
            for channel in self.auto_join_channels:
                self.socket.send(('JOIN '+channel+'\r\n').encode())
    


    def connect(self):
        self.socket.connect((self.network, self.port))
        if self.password:
            self.socket.send(("PASS " + self.password + "\r\n").encode())
        self.socket.send(('NICK '+self.nick+'\r\n').encode())
        self.in_thread.start()
        self.socket.send((" ".join(['USER ', self.user, "0", "*" ,":Piperbot" ]) + '\r\n').encode())
        self.out_thread.start()
        
    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self.ssl:
            self.socket = wrap_socket(self.socket)
        self.socket.bind(('', 0))
        self.in_thread = self.InThread(self.socket, self.in_queue, self.name, self.handlers, self.reconnect)
        self.out_thread = self.OutThread(self.socket, self.out_queue, self.reconnect)
        self.connect()

    class InThread(threading.Thread):
        def __init__(self, serverconnection):
            super(ServerConnection.InThread, self).__init__(daemon=True)
            self.socket = serverconnection.socket
            self.in_queue = serverconnection.in_queue
            self.server_name = serverconnection.name
            self.message_splitter = re.compile(SPLIT_REGEX)
            self.handlers = serverconnection.handlers
            self.onError = serverconnection.reconnect
            self.serverconnection = serverconnection

        def run(self):
            while True:
                try:
                    data = self.socket.recv(4096)
                    lines = data.decode().strip().split("\r\n")
                    for line in lines:
                        if line:
                            msg = Message(self.server_name, *self.message_splitter.match(line).groups(""))
                            if msg.command in self.handlers:
                                self.handlers[msg.command](self.serverconnection)
                            self.in_queue.put(msg)
                except Exception as e:
                    print("ERROR IN " + self.name+" IN THREAD, " + str(e))
                    self.onError()
                    break
                    
    class OutThread(threading.Thread):
        def __init__(self, out_socket, out_queue, on_error):
            super(ServerConnection.OutThread, self).__init__(daemon=True)
            self.socket = out_socket
            self.out_queue = out_queue
            self.onError = on_error

        def run(self):
            while True:
                try:
                    message = self.out_queue.get()
                    line = message.to_line()
                    if not line.endswith("\n"):
                        line += "\n"
                    self.socket.send(line.encode())
                except Exception as e:
                    print("ERROR IN " + self.name+" OUT THREAD, " + str(e))
                    self.onError()
                    break
                
    def disconnect(self, message=""):
        self.socket.send(('QUIT '+message+'\r\n').encode())
        self.socket.close()
        self.connected = False


