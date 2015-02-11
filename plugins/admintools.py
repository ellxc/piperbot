from plugins.stuff.BasePlugin import *


@plugin(desc="admin commands")
class AdminTools:
    def __init__(self):
        self.connect_regex = re.compile("(?:(\w+): )?(\S+):(\d+)(?: (#\w+(?: +#\w+)*))?")

    @command("connect", adminonly=True)
    def connect(self, message):
        match = self.connect_regex.match(message.text)
        response = message.get_reply()
        if match:
            try:
                name, network, port, channels = match.groups()
                self.bot.connect_to(name if name else network, network, int(port),
                                    self.bot.servers[message.server].nick, channels.split() if channels else None)
                response.text = "connecting to {}!".format(name if name else network)
                yield response
            except Exception as e:
                response.text = str(e)
                yield response
        else:
            response.text = "malformed command!"
            yield response

    @command("join", adminonly=True)
    def join(self, message):
        response = message.get_reply()
        response.text = ""
        response.command = "JOIN"
        for channel in message.text.split():
            if channel and channel[0] in "#&!+":
                response.params = channel
                yield response.copy()

    @command("quit", adminonly=True)
    def quit(self, message):
        self.bot.servers[message.server].disconnect(message.text)
        del self.bot.servers[message.server]
        if len(self.bot.servers) == 0:
            self.bot.shutdown()

    @command("leave", adminonly=True)
    def leave(self, message):
        response = message.get_reply()
        response.text = ""
        response.command = "PART"
        if message.text.strip():
            for channel in message.text.split():
                if channel and channel[0] in "#&!+":
                    response.params = channel
                    yield response.copy()
        else:
            yield response

    @command("load", adminonly=True)
    def load(self, message):
        response = message.get_reply()
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.load_plugin_from_module(plugin)
                    response.text = "Loaded plugin(s) " + plugin
                    yield response
                except Exception as e:
                    response.text = "error: " + str(e)
                    yield response

    @command("unload", adminonly=True)
    def unload(self, message):
        response = message.get_reply()
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    response.text = "Unloaded plugin(s) " + plugin
                    yield response
                except Exception as e:
                    response.text = "error: " + str(e)
                    yield response

    @command("reload", adminonly=True)
    def reload(self, message):
        response = message.get_reply()
        if message.text.strip():
            for plugin in message.text.split():
                try:
                    self.bot.unload_module(plugin)
                    self.bot.load_plugin_from_module(plugin)
                    response.text = "reloaded plugin(s) " + plugin
                    yield response
                except Exception as e:
                    response.text = "error: " + str(e)
                    yield response

    @command("eval", adminonly=True)
    def eval(self, message):
        response = message.get_reply()
        try:
            response.text = str(eval(message.text))
            yield response
        except Exception as e:
            response.text = str(e)
            yield response

    @command("exec", adminonly=True)
    def execer(self, message):
        response = message.get_reply()
        try:
            exec(message.text)
            #response.text = "done"
            #yield response
        except Exception as e:
            response.text = str(e)
            yield response