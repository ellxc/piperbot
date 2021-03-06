from wrappers import *
from Message import Message

@plugin(desc="admin commands")
class AdminTools:
    def __init__(self):
        self.connect_regex = re.compile("(?:(\w+): )?(\S+):(\d+)(?: (#\w+(?: +#\w+)*))?")

    @command(groups="^(\S+)$", adminonly=True)
    def nick(self, message):
        x = message.copy()
        x.nick = message.text.split()[0]
        x.text = None
        return x

    @command("notice",adminonly=True)
    def notice(self,message):
        temp = message.copy()
        temp.command = "NOTICE"
        return temp

    @command("unalias", adminonly=True)
    def delalias(self, message):
        assert len(message.data.split()) == 1

    @command("join", adminonly=True)
    def join(self, message):
        response = message.reply("")
        response.command = "JOIN"
        for channel in message.text.split():
            if channel and channel[0] in "#&!+":
                response.params = channel
                yield response

    @command("quit", adminonly=True)
    def quit(self, message):
        self.bot.servers[message.server].disconnect(message.text)
        del self.bot.servers[message.server]
        if len(self.bot.servers) == 0:
            self.bot.shutdown()

    @command("leave")
    def leave(self, message):
        if message.text.strip() and message.text.split():
            for channel in message.text.split():
                if channel and channel[0] in "#&!+":
                    yield Message(server=message.server, params=channel, command="PART", text="cya!")
        else:
            yield Message(server=message.server, params=message.params, command="PART", text="cya!")

    @command("load", adminonly=True)
    def load(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.load_plugin_from_module(plugin)
                    return message.reply("Loaded plugin(s) " + plugin)
                except Exception as e:
                    return message.reply("error: " + str(e))

    @command("unload", adminonly=True)
    def unload(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    return message.reply("Unloaded plugin(s) " + plugin)
                except Exception as e:
                    return message.reply("error: " + str(e))

    @command("reload", adminonly=True)
    def reload(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    self.bot.load_plugin_from_module(plugin)
                    return message.reply("reloaded plugin(s) " + plugin)
                except Exception as e:
                    return message.reply("error: " + str(e))

    @command("eval", adminonly=True)
    def eval(self, message):
        try:
            result = eval(message.text)
            return message.reply(result, str(result))
        except Exception as e:
            return message.reply(str(type(e)) + ": " + str(e))

    @command("exec", adminonly=True)
    def execer(self, message):
        try:
            exec(message.text)
        except Exception as e:
            return message.reply(str(e))
