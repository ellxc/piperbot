from plugins.stuff.BasePlugin import *
from Message import Message, RawLine

@plugin(desc="testing module 1234")
class testing1:

    # @onLoad
    # def startup(self):
        # print("STARTING")
        
    # @onUnload
    # def shutdown(self):
        # print("stopping")

    # @trigger(Message.isNotice)
    # def meepswdefs(self,message):
        # response = message.get_reply()
        # response.command = "PRIVMSG"
        # response.text = "I noticed your notice"
        # yield response
        
    # @trigger(lambda m: Message.isMessage(m) and m.nick == "Penguin")
    # def onPenguin(self,message):
        # response = message.get_reply()
        # response.text = "Penguin is the best"
        # yield response
        


    @command
    def meep(self,message):
        response = message.get_reply()
        response.text = "meep"
        yield response

    @command("nick")
    def nick(self,message):
        response = message.get_reply()
        response.text = "My nick is {}".format(self.bot.servers[message.server].nick)
        yield response

@plugin(desc="testing module 1234")
class testing2:

    @command("test")
    def test(self,message):
        yield RawLine(message.server,"PRIVMSG #bottesting :rawstring")

    @regex("^<(.*?)>$")
    def regextest(self,message):
        response = message.get_reply()
        # response.text = "derp" # message.groups[0]
        response.text = message.groups[0]
        yield response

    @command("admin",adminonly = True)
    def admin(self,message):
        response = message.get_reply()
        response.text = "admin"
        yield response