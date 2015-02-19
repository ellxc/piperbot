from wrappers import *
from Message import Message

@plugin
class serverutils:

    @event("001")
    def autojoin(self, message):
        for channel in self.bot.servers[message.server].auto_join_channels:
            yield Message(server=message.server, command="JOIN", params=channel)