from wrappers import *


@plugin
class Users:

    def __init__(self):
        self.users = {}
        self.channels = {}

    def newuser(self, server, nick):
        self.newserv(server)
        if nick not in self.users[server]:
            self.users[server][nick] = {}

    def newchan(self, server, chan):
        self.newserv(server)
        if chan not in self.channels[server]:
            self.channels[server][chan] = set()

    def newserv(self, server):
        if server not in self.users:
            self.users[server] = {}
        if server not in self.channels:
            self.channels[server] = {}

    @event("001")
    def joinserv(self, message):
        self.newuser(message.server, message.params)

    @event("353")
    def names(self, message):
        self.newchan(message.server, message.params.split()[-1])
        for nick in message.text.split():
            if nick.startswith("+"):
                nick = nick[1:]
            if nick.startswith("@"):
                nick = nick[1:]

            self.newuser(message.server, nick)
            self.users[message.server][nick][message.params.split()[-1]] = True
            self.channels[message.server][message.params.split()[-1]].add(nick)

    @event("JOIN")
    def onjoin(self, message):

        if message.nick.startswith("+"):
            nick = message.nick[1:]
        elif message.nick.startswith("@"):
            nick = message.nick[1:]
        else:
            nick = message.nick

        self.newuser(message.server, nick)
        self.newchan(message.server, (message.params or message.text))

        self.users[message.server][nick][(message.params or message.text)] = True
        self.channels[message.server][(message.params or message.text)].add(nick)

    @event("PART")
    def onpart(self, message):
        if message.nick.startswith("+"):
            nick = message.nick[1:]
        elif message.nick.startswith("@"):
            nick = message.nick[1:]
        else:
            nick = message.nick
        del self.users[message.server][nick][(message.params or message.text)]
        self.channels[message.server][(message.params or message.text)].remove(nick)

    @event("QUIT")
    def onquit(self, message):
        if message.nick.startswith("+"):
            nick = message.nick[1:]
        elif message.nick.startswith("@"):
            nick = message.nick[1:]
        else:
            nick = message.nick

        del self.users[message.server][nick]
        self.channels[message.server][(message.params or message.text)].remove(nick)

    @command("nicks")
    def nicks(self, message):
        nicks = [nick for nick in self.channels[message.server][message.params]]
        yield message.reply(data=nicks, text=" ".join(nicks))

