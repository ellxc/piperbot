from wrappers import *
from Message import Message
import time

@plugin(desc="testing module 1234")
class testing1:

    @command
    def meep(self, message):
        yield message.reply("meep")


@plugin(desc="testing module 1234")
class testing2:

    @command("argtest", groups="(.)(.*)")
    def argtest(self, message):
        yield message.reply(str(message.groups))

    @command("test")
    def test(self, message):
        yield message.reply("your message: " + str(message))


    @command("data")
    def data(self, message):
        yield message.reply("your message's data is: " + repr(str(message.data)))

    @regex("^<(.*?)>$")
    def regextest(self, message):
        yield message.reply(message.groups[0])

    @command("admin", adminonly=True)
    def admin(self, message):
        yield message.reply("yes {}, you are an admin!".format(message.nick))