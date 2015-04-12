from wrappers import *
from Message import Message

@plugin
class serverutils:

    @event("001")
    def autojoin(self, message):
        for channel in self.bot.servers[message.server].auto_join_channels:
            yield Message(server=message.server, command="JOIN", params=channel)

    @event("JOIN")
    def channeljoined(self, message):
        if message.nick == self.bot.servers[message.server].nick:
            self.bot.servers[message.server].channels.append(message.params or message.text)


    @event("PART")
    def channelleft(self, message):
        if message.nick == self.bot.servers[message.server].nick:
            self.bot.servers[message.server].channels.remove(message.params or message.text)