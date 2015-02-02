import datetime
import copy

class RawLine():
    def __init__(self, server, string):
        self.server = server
        self.string = string

    def copy(self):
        return RawLine(self.server, self.string)

    def to_line(self):
        return self.string


class Message():
    def __init__(self, server="", nick="", user="", domain="", command="", params="", action="", text="",
                 timestamp=None, raw="" , groups = None):
        self.server = server
        self.nick = nick
        self.user = user
        self.domain = domain
        self.command = command
        self.params = params
        self.action = action
        if action: self.text = text[:-1]
        else: self.text = text
        self.raw = raw
        self.groups = groups
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.datetime.now()

    def to_line(self):
        if self.action and self.command == "PRIVMSG":
            return self.command + " " + self.params + ((" :\001ACTION " + self.text) if self.text else "")
        else:
            return self.command + " " + self.params + ((" :" + self.text) if self.text else "")
            
    def reply(self,text):
        return Message(server=self.server, command=self.command, params=self.params, text=text)

    def get_reply(self):
        return Message(server=self.server, command=self.command, params=self.params, text=self.text)

    def copy(self):
        return copy.copy(self)

    def __lt__(self, other):
        return (self.action and not other.action) or self.timestamp < other.timestamp

    def __str__(self):
        return "{}: {}{} {} {}:{}".format(self.server, str(self.timestamp)[:-7], (
        " <" + self.nick + "(" + self.user + ("@" if self.user else "") + self.domain + ")>") if self.domain else "",
                                          "ACTION " if self.action else self.command, self.params, self.text)

    def to_raw(self):
        if self.raw:
            return RawLine(self.server, self.raw)
        else:
            return RawLine(self.server, self.to_line)

    @staticmethod
    def is_ping(msg,bot):
        return msg.command == "PING"

    @staticmethod
    def is_kick(msg,bot):
        return msg.command == "KICK"

    @staticmethod
    def is_nick(msg,bot):
        return msg.command == "NICK"

    @staticmethod
    def is_quit(msg,bot):
        return msg.command == "QUIT"

    @staticmethod
    def is_join(msg,bot):
        return msg.command == "JOIN"

    @staticmethod
    def is_mode(msg,bot):
        return msg.command == "MODE"

    @staticmethod
    def is_part(msg,bot):
        return msg.command == "PART"

    @staticmethod
    def is_topic(msg,bot):
        return msg.command == "TOPIC"

    @staticmethod
    def isInvite(msg,bot):
        return msg.command == "INVITE"

    @staticmethod
    def isNotice(msg,bot):
        return msg.command == "NOTICE"

    @staticmethod
    def isMessage(msg,bot):
        return msg.command == "PRIVMSG" and any(map(msg.params.startswith, ["#", "&", "!", "+", "~"]))

    @staticmethod
    def isPrivateMessage(msg,bot):
        return msg.command == "PRIVMSG" and not any(map(msg.params.startswith, ["#", "&", "!", "+", "~"]))

    @staticmethod
    def isAction(msg,bot):
        return Message.isMessage(msg) and msg.text.startswith("\001ACTION")

    @staticmethod
    def isPrivateAction(msg,bot):
        return Message.isPrivateMessage(msg) and msg.text.startswith("\001ACTION")
    
    
    
    
    