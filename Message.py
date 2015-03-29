import datetime
import copy
import re


SPLIT_REGEX = r"^(?::(?:(?:(?P<nick>\S+)!)?(?:(?P<user>\S+)@)?(?P<domain>\S+) +))?" \
              r"(?P<command>\S+)(?: +(?!:)(?P<params>.+?))?(?: *:(?:\x01(?P<CTCP>\w+) )?(?P<text>.+?))?\x01?$"


class Message():
    def __init__(self, server=None, nick="", user="", domain="", command="", params="", ctcp="", text=None
                 , timestamp=None, groups=None, data=None, args=None):
        self.server = server
        # self.channel = channel
        self.nick = nick
        self.user = user
        self.domain = domain
        self.command = command
        self.params = params
        self.ctcp = ctcp
        if ctcp:
            print(ctcp)
            self.command = ctcp
        self.text = text
        self.timestamp = timestamp or datetime.datetime.now()
        self.groups = groups
        self.data = data
        self.args = args



    @property
    def text(self):
        if self._text is None:
            if self.data is not None:
                return str(self.data)
            return ""
        return self._text

    @text.setter
    def text(self, val):
        if val:
            if val.startswith("\001"):
                cmd, *val = val.split(" ")
                val = " ".join(val)
                self.ctcp = cmd
                if val.endswith("\001"):
                    val = val[:-1]
        self._text = val


    @property
    def command(self):
        if self._command == self.ctcp:
            return "PRIVMSG"
        else:
            return self._command

    @command.setter
    def command(self, val):
        self._command = val

    def to_line(self):
        text = self.text.replace("\r", "").replace("\n", "")
        return "%s %s :%s%s%s" % (
            self.command, self.params, ("\001%s " % self.ctcp if self.ctcp else ""), text,
            ("\001" if self.ctcp else ""))

    def to_pretty(self):
        text = self.timestamp.strftime("%x %X")
        text += " "
        if self.ctcp:
            text += " * %s " % self.nick
        else:
            text += "< %s> " % self.nick
        text += self.text.rstrip("\n")
        return text

    def reply(self, data=None, text=None, args=None):
        return Message(server=self.server, nick=self.nick, command=self.command,
                       domain=self.domain, ctcp=self.ctcp, groups=self.groups, user=self.user,
                       params=self.params, text=text, data=data, args=args)

    def copy(self):
        return copy.copy(self)

    def __lt__(self, other):
        return (self.command.lower() == "ping" and not other.command.lower() == "ping") \
               or self.timestamp < other.timestamp

    def __str__(self):
        return "{}: {}{} {} {}:{}".format(self.server, str(self.timestamp)[:-7],
                                          (" <" + self.nick + "(" + self.user + ("@" if self.user else "")
                                           + self.domain + ")>")
                                          if self.domain else "", self.ctcp if self.ctcp else self.command,
                                          self.params, self.text)


    @staticmethod
    def from_line(line, server):
        if not line:
            return
        else:
            return Message(server, *re.match(SPLIT_REGEX, line).groups(""))

    @staticmethod
    def is_ping(msg, bot):
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
