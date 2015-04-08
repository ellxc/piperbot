from wrappers import *
import time

@plugin(desc="testing module 1234")
class testing1:

    @command
    def meep(self, message):
        return message.reply("meep")


@plugin(desc="testing module 1234")
class testing2:

    @command("argtest", groups="(.)(.*)")
    def argtest(self, message):
        return message.reply(str(message.groups))

    @command("test")
    def test(self, message):
        return message.reply("your message: " + str(message))


    @command("data")
    def data(self, message):
        return message.reply("your message's data is: " + repr(str(message.data)))

    @regex("^<(.*?)>$")
    def regextest(self, message):
        return message.reply(message.groups)

    @command("admin", adminonly=True)
    def admin(self, message):
        return message.reply("yes {}, you are an admin!".format(message.nick))


    @adv_command("time")
    def timer(self, arg, target):
        start = time.perf_counter()
        try:
            while 1:
                x = yield
        except GeneratorExit:
            total = time.perf_counter() - start
            target.send(arg.reply(total, "took %s seconds" % total))
            target.close()
