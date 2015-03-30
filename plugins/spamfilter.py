

import urllib.parse
import urllib.response
import urllib.request

from wrappers import *
from Message import Message
from collections import defaultdict
from datetime import datetime, timedelta


@plugin
class spamfilter:

    def __init__(self):
        self.spamlimit = 3
        self.pmspamlimit = 3
        self.bots = ["Gwyn", "CirnoX", "Kuddle_Kitty", "cake"]
        self.spams = defaultdict(lambda: defaultdict(lambda: False))


    @extension(priority=997, type=extensiontype.command)
    @extension(priority=997, type=extensiontype.regex)
    @extension(priority=997, type=extensiontype.event)
    @extension(priority=997, type=extensiontype.trigger)
    def spamcheck(self, orginal, target):
        time = datetime.now()
        try:
            while 1:
                message = yield
                if message.command in ["PRIVMSG", "ACTION", "NOTICE"]:
                    if self.spams[message.server][message.params]:
                        if time - self.spams[message.server][message.params] < timedelta(seconds=30):
                            continue
                target.send(message)
        except GeneratorExit:
            target.close()

    @command("spam", simple=True)
    def stopspam(self, message):
        yield message.reply("sorry, I will be quiet for a while")
        self.spams[message.server][message.params] = datetime.now()

    @extension(priority=-999, type=extensiontype.command)
    @extension(priority=-999, type=extensiontype.regex)
    def botfilter(self, message):
        if message.nick in self.bots:
            return
        else:
            return message

    @extension(priority=999,type=extensiontype.command)
    def spamfilter(self, original, target):
        spams = defaultdict(lambda: defaultdict(list))
        try:
            while 1:
                x = yield
                if x.params.startswith("#"):
                    spams[x.server][x.params].append(x.text)
                    if len(spams[x.server][x.params]) <= self.spamlimit:
                        target.send(x)
                else:
                    spams[x.server][x.params].append(x.text)
                    if len(spams[x.server][x.params]) <= self.pmspamlimit:
                        target.send(x)
        except GeneratorExit:
            for server, messages in spams.items():
                for channel, lines in messages.items():
                    if channel.startswith("#"):
                        spamlimit = self.spamlimit
                    else:
                        spamlimit = self.pmspamlimit
                    if len(lines) > spamlimit:
                        data = {'sprunge': '\n'.join(lines)}
                        response = urllib.request.urlopen(urllib.request.Request('http://sprunge.us', urllib.parse.urlencode(data).encode('utf-8'))).read().decode()
                        target.send(Message(server=server, params=channel,command="PRIVMSG", text="spam detected, here is the output: %s" % response))
            target.close()

    @extension(priority=998,type=extensiontype.command)
    def toolarge(self, message):

        if len(bytearray(message.text.encode('utf-8'))) > 1000:
            message.text = "message too large, here is the output: " + urllib.request.urlopen(urllib.request.Request('http://sprunge.us', urllib.parse.urlencode({'sprunge': message.text}).encode('utf-8'))).read().decode()
        return message
