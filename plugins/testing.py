from plugins.stuff.BasePlugin import *
from Message import Message
import time

@plugin(desc="testing module 1234")
class testing1:

    @command
    def meep(self, message):
        yield message.reply("meep")

    @command("nick")
    def nick(self, message):
        yield message.reply("My nick is {}".format(self.bot.servers[message.server].nick))

@plugin(desc="testing module 1234")
class testing2:

    @command("test")
    def test(self, message):
        yield message.reply("your message: " + str(message))

    @regex("^<(.*?)>$")
    def regextest(self, message):
        yield message.reply(message.groups[0])

    @command("admin", adminonly=True)
    def admin(self, message):
        yield message.reply("yes {}, you are an admin!".format(message.nick))