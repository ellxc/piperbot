import socket
from queue import PriorityQueue
import threading
import re
from Message import Message
import time
from ssl import wrap_socket

SPLIT_REGEX = r"^(?::(?:(?:(\S+)!)?(?:(\S+)@)?(\S+) ))?(\S+)(?: (?!:)(.+?))?(?: :(\x01ACTION )?(.+))?$"


class ServerConnection():
    def __init__(self, queue, name, network, port, nick, password=None, username=None, ircname = None, channels=None,ssl=False):



        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )

        if ssl:
            self.socket = wrap_socket(self.socket)

        self.socket.bind(('', 0))


        self.in_queue = queue
        self.out_queue = PriorityQueue()
        self.connected = False

        
        self.in_thread = self.InThread(self.socket, self.in_queue, name, self.reconnect)
        self.out_thread = self.OutThread(self.socket, self.out_queue, self.reconnect)
        
        self.name = name
        self.network = network
        self.port = port
        self.nick = nick
        self.user = username or nick
        self.ircname = ircname or nick
        self.password = password
        self.channels = channels if channels else []

    def connect(self):
        self.socket.connect((self.network, self.port))

        if self.password:
            self.socket.send(("PASS " + self.password + "\r\n").encode())

        self.socket.send(('NICK '+self.nick+'\r\n').encode())

        self.in_thread.start()

        self.socket.send((" ".join(['USER ', self.user, "0", "*" ,":Piperbot" ]) + '\r\n').encode())

        #for line in self.socket.recv(4096).decode().split('\r\n'):
        #    print(self.name + ": " + line)

        for channel in self.channels:
            self.socket.send(('JOIN '+channel+'\r\n').encode())

        self.out_thread.start()
        
    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.network, self.port))
        for line in self.socket.recv(4096).decode().split('\r\n'):
            print(self.name + ": " + line)
        self.socket.send(('NICK '+self.nick+'\r\n').encode())
        self.socket.send(('USER '+(self.nick+' ')*3+'Python IRC\r\n').encode())
        for channel in self.channels:
            self.socket.send(('JOIN '+channel+'\r\n').encode())

        self.in_thread = self.InThread(self.socket, self.in_queue, self.name, self.reconnect)
        self.out_thread = self.OutThread(self.socket, self.out_queue, self.reconnect)
        self.in_thread.start()
        self.out_thread.start()

    class InThread(threading.Thread):
        def __init__(self, in_socket, in_queue, server_name, on_error):
            super(ServerConnection.InThread, self).__init__(daemon=True)
            self.socket = in_socket
            self.in_queue = in_queue
            self.server_name = server_name
            self.message_splitter = re.compile(SPLIT_REGEX)
            self.onError = on_error

        def run(self):
            while True:
                try:
                    data = self.socket.recv(4096)
                    lines = data.decode().strip().split("\r\n")
                    for line in lines:
                        if line:
                            self.in_queue.put(Message(self.server_name, *self.message_splitter.match(line).groups("")))
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
