from wrappers import *
from scheduler import Task
from Message import Message

@plugin
class Leet:
    @scheduled(Task.every().day.at("13:37"))
    def l33t(self):
        for servername, server in self.bot.servers.items():
            for channel in server.channels:
                self.bot.send(Message(server=servername, params=channel, command="PRIVMSG", text="LEET TIME"))