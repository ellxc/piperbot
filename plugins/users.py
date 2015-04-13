from wrappers import *


@plugin
class Users:
    @event("353")
    def names(self, message):
        for nick in message.text.split():
            if nick.startswith("+"):
                nick = nick[1:]
            if nick.startswith("@"):
                nick = nick[1:]
                self.bot.ops[message.server][message.params.split()[-1]].add(nick)
            self.bot.users[message.server][nick].channels[message.server].append(message.params.split()[-1])

    @event("JOIN")
    def onjoin(self, message):
        if message.nick.startswith("+"):
            nick = message.nick[1:]
        elif message.nick.startswith("@"):
            nick = message.nick[1:]
            self.bot.ops[message.server][message.params.split()[-1]].add(nick)
        else:
            nick = message.nick

        self.bot.users[message.server][nick].channels[message.server].append(message.params.split()[-1])

    @event("PART")
    def onpart(self, message):
        if message.nick.startswith("+"):
            nick = message.nick[1:]
        elif message.nick.startswith("@"):
            nick = message.nick[1:]
            self.bot.ops[message.server][message.params.split()[-1]].remove(nick)
        else:
            nick = message.nick
        self.bot.users[message.server][nick].channels[message.server].remove(message.params.split()[-1])

    @event("QUIT")
    def onquit(self, message):
        self.bot.users[message.server][message.nick].channels[message.server] = []



    @command("channels")
    def channels(self, message):
        if len(message.text.split()) == 1:
            if message.text in self.bot.users[message.server]:
                return message.reply(("I see %s in these channels: " % message.text) +
                                    ", ".join(self.bot.users[message.server][message.text].channels[message.server]))
        elif len(message.text.split()) == 0:
            return message.reply("I see you in these channels: " +
                                ", ".join(self.bot.users[message.server][message.nick].channels[message.server]))

    @command("nicks")
    def nicks(self, message):
        nicks = [nick for nick, user in self.bot.users[message.server].items() if message.params in user.channels[message.server]]
        yield message.reply(data=nicks, text=" ".join(nicks))

