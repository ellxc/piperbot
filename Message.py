import datetime
import copy
import re


SPLIT_REGEX = r"^(?::(?:(?:(?P<nick>\S+)!)?(?:(?P<user>\S+)@)?(?P<domain>\S+) +))?" \
              r"(?P<command>\S+)(?: +(?!:)(?P<params>.+?))?(?: *:(?P<action>\x01ACTION )?(?P<text>.+?))?\x01?$"

class Message():
    def __init__(self, server=None, nick="", user="", domain="", command="", params="", action="", text=""
                 , timestamp=None, groups = None):
        self.server = server
        #self.channel = channel
        self.nick = nick
        self.user = user
        self.domain = domain
        self._command = command
        self.params = params
        self.action = action
        self._text = text
        self.timestamp = timestamp or datetime.datetime.now()
        self.groups = groups

    @property
    def text(self):
        #if self.action and self.command == "PRIVMSG" or self.command == "ACTION":
        #    return "\001ACTION " +self._text +"\001"
        #else:
        return self._text

    @text.setter
    def text(self,val):
        if val.startswith("\001ACTION"):
            val = val[6:]
            self.action = True
            
            if val.endswith("\001"):
                val = val[:-1]
    
        self._text = val

    @property
    def command(self):
        if self._command == "ACTION":
            return "PRIVMSG"
        else:
            return self._command

    @command.setter
    def command(self, val):
        self._command = val

    def to_line(self):
        return "%s %s :%s%s%s" % (self.command,self.params,("\001ACTION " if self.action else ""),self.text,("\001" if self.action else ""))

    def reply(self, text=None):
        return Message(server=self.server, nick=self.nick, command=self.command, 
        domain=self.domain, action=self.action, groups=self.groups, 
        params=self.params, text=text if text is not None else self.text)

    def copy(self):
        return copy.copy(self)

    def __lt__(self, other):
        return (self.command.lower() == "ping" and not other.command.lower() == "ping") \
                or self.timestamp < other.timestamp

    def __str__(self):
        return "{}: {}{} {} {}:{}".format(self.server, str(self.timestamp)[:-7],
                                        (" <" + self.nick + "(" + self.user + ("@" if self.user else "")
                                         + self.domain + ")>")
                if self.domain else "", "ACTION " if self.action else self.command, self.params, self.text)


    @staticmethod
    def from_line(line):
        if not line:
            return
        else:
            return Message("",*re.match(SPLIT_REGEX,line).groups(""))



    @staticmethod
    def is_ping(msg,bot):
        return msg.command == "PING"

    @staticmethod
    def is_kick(msg, bot):
        return msg.command == "KICK"

    @staticmethod
    def is_nick(msg, bot):
        return msg.command == "NICK"

    @staticmethod
    def is_quit(msg, bot):
        return msg.command == "QUIT"

    @staticmethod
    def is_join(msg, bot):
        return msg.command == "JOIN"

    @staticmethod
    def is_mode(msg, bot):
        return msg.command == "MODE"

    @staticmethod
    def is_part(msg, bot):
        return msg.command == "PART"

    @staticmethod
    def is_topic(msg, bot):
        return msg.command == "TOPIC"

    @staticmethod
    def is_invite(msg, bot):
        return msg.command == "INVITE"

    @staticmethod
    def is_notice(msg, bot):
        return msg.command == "NOTICE"

    @staticmethod
    def is_message(msg, bot):
        return msg.command == "PRIVMSG" and any(map(msg.params.startswith, ["#", "&", "!", "+", "~"]))

    @staticmethod
    def is_private_message(msg, bot):
        return msg.command == "PRIVMSG" and not any(map(msg.params.startswith, ["#", "&", "!", "+", "~"]))

    @staticmethod
    def is_action(msg, bot):
        return Message.is_message(msg, bot) and msg.text.startswith("\001ACTION")

    @staticmethod
    def is_private_action(msg, bot):
        return Message.is_private_message(msg, bot) and msg.text.startswith("\001ACTION")
