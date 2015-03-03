import socket
from queue import PriorityQueue
import threading
import re
from ssl import wrap_socket

from Message import Message


SPLIT_REGEX = r"^(?::(?:(?:(?P<nick>\S+)!)?(?:(?P<user>\S+)@)?(?P<domain>\S+) +))?" \
              r"(?P<command>\S+)(?: +(?!:)(?P<params>.+?))?(?: *:(?P<action>\x01ACTION )?(?P<text>.+?))?\x01?$"


class ServerConnection():
    def __init__(self, queue, name, network, port, nick, password=None, username=None, ircname=None,
                 auto_join_channels=None, ssl=False):
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

        self.socket = socket.socket()
        if self.ssl:
            self.socket = wrap_socket(self.socket)
        self.socket.bind(('', 0))
        self.in_thread = self.InThread(self)

    def connect(self):
        self.connected = True
        self.socket.connect((self.network, self.port))
        self.in_thread.start()
        if self.password:
            self.socket.send(("PASS " + self.password + "\r\n").encode())
        self.socket.send(('NICK ' + self.nick + '\r\n').encode())
        self.socket.send((" ".join(['USER ', self.user, "0", "*", ":Piperbot"]) + '\r\n').encode())

    def reconnect(self):
        self.socket = socket.socket()
        if self.ssl:
            self.socket = wrap_socket(self.socket)
        self.socket.bind(('', 0))
        self.in_thread = self.InThread(self)
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
                    try:
                        data = data.decode()
                        lines = data.strip().split("\r\n")
                        for line in lines:
                            if line:
                                msg = Message(self.server_name, *self.message_splitter.match(line).groups(""))
                                self.in_queue.put(msg)
                    except Exception as e:
                        print("ERROR IN " + self.name + " INTHREAD, " + str(e))
                except Exception as e:
                    print("ERROR IN " + self.name + " INTHREAD, " + str(e))
                    if self.serverconnection.connected:
                        self.onError()
                    break


    def disconnect(self, message=""):
        self.socket.send(('QUIT ' + message + '\r\n').encode())
        self.socket.close()
        self.connected = False


