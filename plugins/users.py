from wrappers import *
from collections import defaultdict


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

    @command("channels")
    def channels(self, message):
        if len(message.text.split()) == 1:
            if message.text in self.bot.users[message.server]:
                yield message.reply(("I see %s in these channels: " % message.text) +
                                    ", ".join(self.bot.users[message.server][message.text].channels[message.server]))
        elif len(message.text.split()) == 0:
            yield message.reply("I see you in these channels: " +
                                ", ".join(self.bot.users[message.server][message.nick].channels[message.server]))
