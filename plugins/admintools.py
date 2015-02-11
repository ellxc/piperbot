from plugins.stuff.BasePlugin import *


@plugin(desc="admin commands")
class AdminTools:
    def __init__(self):
        self.connect_regex = re.compile("(?:(\w+): )?(\S+):(\d+)(?: (#\w+(?: +#\w+)*))?")

    @command("connect", adminonly=True)
    def connect(self, message):
        match = self.connect_regex.match(message.text)
        if match:
            try:
                name, network, port, channels = match.groups()
                self.bot.connect_to(name if name else network, network, int(port),
                                    self.bot.servers[message.server].nick, channels.split() if channels else None)
                response.text = "connecting to {}!".format(name if name else network)
                yield response
            except Exception as e:
                yield message.reply(str(e))
        else:
            yield message.reply("malformed command!")

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

    @command("leave", adminonly=True)
    def leave(self, message):
        response = message.reply("")
        response.command = "PART"
        if message.text.strip():
            for channel in message.text.split():
                if channel and channel[0] in "#&!+":
                    response.params = channel
                    yield response
        else:
            yield response

    @command("load", adminonly=True)
    def load(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.load_plugin_from_module(plugin)
                    yield message.reply("Loaded plugin(s) " + plugin)
                except Exception as e:
                    yield message.reply("error: " + str(e))

    @command("unload", adminonly=True)
    def unload(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    yield message.reply("Unloaded plugin(s) " + plugin)
                except Exception as e:
                    yield message.reply("error: " + str(e))

    @command("reload", adminonly=True)
    def reload(self, message):
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    self.bot.load_plugin_from_module(plugin)
                    yield message.reply("reloaded plugin(s) " + plugin)
                except Exception as e:
                    yield message.reply("error: " + str(e))

    @command("eval", adminonly=True)
    def eval(self, message):
        try:
            yield message.reply(str(eval(message.text)))
        except Exception as e:
            yield message.reply(str(e))

    @command("exec", adminonly=True)
    def execer(self, message):
        try:
            exec(message.text)
        except Exception as e:
            yield message.reply(str(e))