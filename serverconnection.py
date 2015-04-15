import socket
import threading
from ssl import wrap_socket
from select import select

from Message import Message


SPLIT_REGEX = r"^(?::(?:(?:(?P<nick>\S+)!)?(?:(?P<user>\S+)@)?(?P<domain>\S+) +))?" \
              r"(?P<command>\S+)(?: +(?!:)(?P<params>.+?))?(?: *:(?P<action>\x01ACTION )?(?P<text>.+?))?\x01?$"


class ServerConnection():
    def __init__(self, queue, name, network, port, nick, password=None, username=None, ircname=None,
                 auto_join_channels=None, ssl=False):
        self.in_queue = queue
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
        self.channels = []

        self.socket = socket.socket()
        if self.ssl:
            self.socket = wrap_socket(self.socket)
        self.socket.bind(('', 0))
        self.in_thread = self.InThread(self)

    def connect(self):
        self.connected = True

        # Attempt to create a new socket to the host, and print an error on failure.
        try:
            self.socket.connect((self.network, self.port))
        except Exception as e:
            print("Failed to creat socket to {}:{}".format(self.network, self.port))
            raise e

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
            super(ServerConnection.InThread, self).__init__()
            self.socket = serverconnection.socket
            self.in_queue = serverconnection.in_queue
            self.server_name = serverconnection.name
            self.onError = serverconnection.reconnect
            self.serverconnection = serverconnection

        def run(self):
            while self.serverconnection.connected:
                try:
                    readable, writable, ex = select([self.socket], [], [self.socket], 1)
                    if readable:
                        data = readable[0].recv(4096)
                        try:
                            data = data.decode()
                            lines = data.strip().split("\r\n")
                            for line in lines:
                                if line:
                                    msg = Message.from_line(line, self.server_name)
                                    if msg.command == "PRIVMSG" and msg.params == self.serverconnection.nick:
                                        msg.params = msg.nick  # account for prviate messages
                                    self.in_queue.put(msg)
                        except Exception as e:
                            print("ERROR IN " + self.name + " INTHREAD, " + str(e))
                    if ex:
                        raise Exception("error in socket")
                except Exception as e:
                    print("ERROR IN " + self.name + " INTHREAD, " + str(e))
                    if self.serverconnection.connected:
                        self.onError()
                    break


    def disconnect(self, message=""):
        try:
            self.socket.send(('QUIT :' + message + '\r\n').encode())
            self.socket.close()
        except BrokenPipeError:
            pass  # assume socket closed
        self.connected = False


