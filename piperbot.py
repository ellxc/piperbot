import re
from collections import defaultdict, deque
import threading
from multiprocessing.pool import ThreadPool
from queue import PriorityQueue, Empty
import inspect
import importlib
import os
import json
import codecs
from sys import argv
from serverconnection import ServerConnection



class User:
    def __init__(self):
        self.channels = defaultdict(list)
        self.data = {}


class PiperBot(threading.Thread):
    def __init__(self):
        super(PiperBot, self).__init__(daemon=True)

        self.servers = {}

        self.admins = defaultdict(list)
        self.users = defaultdict(lambda: defaultdict(User))
        self.ops = defaultdict(lambda: defaultdict(set))

        self.command_char = "#"
        self.in_queue = PriorityQueue()

        self.commands = {}
        self.plugins = {}

        self.worker_pool = ThreadPool(processes=4)

        self.message_buffer = defaultdict(lambda: defaultdict(lambda: deque(maxlen=50)))
        self.buffer_pattern = re.compile(r"(?:(\w+)|(\s)|^)(?:\^(\d+)|(\^+))")
        self.buffer_pattern_escape = re.compile(r"\\\^")

        self.running = False


    def buffer_replace(self, text, servername, channel, offset=0):

        buffer = list(self.message_buffer[servername][channel])[offset:]

        def buffer_sub(match_object):
            if match_object.group(1):
                messgages = [x for x in buffer if x.nick == match_object.group(1)]
                if not messgages:
                    raise Exception("user not in memory")
            else:
                messgages = buffer
            if match_object.group(3):
                count = int(match_object.group(3))
            elif match_object.group(4):
                count = len(match_object.group(4))
            if count <= len(messgages):
                return (" " if match_object.group(2) else "") + messgages[count - 1].text
            else:
                raise Exception("line not in memory")

        text = self.buffer_pattern.sub(buffer_sub, text)
        text = self.buffer_pattern_escape.sub("^", text)
        return text

    def connect_to(self, servername, network, port, nick, channels=None, admins=None, password=None, username=None,
                   ircname=None, ssl=False):
        self.servers[servername] = ServerConnection(self.in_queue, servername, network, port, nick, password, username,
                                                    ircname, channels, ssl)
        self.servers[servername].connect()
        if admins:
            self.admins[servername] += admins

    def run(self):
        self.running = True
        try:
            while self.running:
                try:
                    message = self.in_queue.get(timeout=10)
                    print("<< " + str(message))
                    self.handle_message(message)
                except Empty:
                    pass
        finally:
            self.shutdown()

    def shutdown(self):
        self.running = False
        for plugin in self.plugins.values():
            for func in plugin._onUnloads:
                func()
        for server in self.servers.values():
            server.disconnect(message="shutting down")

    def load_plugin_from_module(self, plugin):
        if "." in plugin:
            module = "".join(plugin.split(".")[:-1])
            plugin_name = plugin.split(".")[-1]
            temp = importlib.machinery.SourceFileLoader(module, os.path.dirname(
                os.path.abspath(__file__)) + "/plugins/" + module + ".py").load_module()
            found = False
            for name, Class in inspect.getmembers(temp, lambda x: inspect.isclass(x) and hasattr(x, "_plugin")):
                if name == plugin_name:
                    self.load_plugin(Class)
                    found = True
            if not found:
                raise Exception("no such plugin to load")
        else:
            temp = importlib.machinery.SourceFileLoader(plugin, os.path.dirname(
                os.path.abspath(__file__)) + "/plugins/" + plugin + ".py").load_module()
            found = False
            for name, Class in inspect.getmembers(temp, lambda x: inspect.isclass(x) and hasattr(x, "_plugin")):
                self.load_plugin(Class)
                found = True
            if not found:
                raise Exception("no such plugin to load")

    def unload_module(self, module_name):
        found = False
        plugins = []
        for plugin_name, plugin in self.plugins.items():
            if plugin_name.startswith(module_name + ".") or plugin_name == module_name:
                plugins.append(plugin_name)
                found = True
        for plugin in plugins:
            self.unload_plugin(plugin)
        if not found:
            raise Exception("no such plugin to unload")

    def load_plugin(self, plugin):
        if plugin.__module__ + "." + plugin.__name__ in self.plugins:
            raise Exception("already loaded!")
        plugin_instance = plugin()
        plugin_instance._plugin__init__(self)
        for func in plugin_instance._onLoads:
            func()
        self.plugins[plugin_instance.__module__ + "." + plugin_instance.__class__.__name__] = plugin_instance
        for (func, args) in plugin_instance._commands:
            if args["command"] not in self.commands:
                self.commands[args["command"]] = (func, args)
                print("loaded command: ", args["command"])
            else:
                print("command overlap! : " + args["command"])
        if plugin._plugin_thread:
            plugin_instance.start()

    def unload_plugin(self, plugin_name):
        for func, args in self.plugins[plugin_name]._commands:
            if args["command"] in self.commands.keys():
                del self.commands[args["command"]]
        for func in self.plugins[plugin_name]._onUnloads:
            func()
        del self.plugins[plugin_name]

    def handle_message(self, message):
        if message.command == "PING":
            response = message.copy()
            response.command = "PONG"
            self.send(response)
        elif message.command == "PRIVMSG":
            if message.text.startswith(self.command_char) and message.text[1:]:
                print("command: ", message.text[1:])

                commands = map(lambda x: [(command, " ".join(args)) for command, *args in [x.split(" ")]][0],
                               map(lambda x: x.strip(), message.text[1:].split(" || ")))
                funcs = []
                args = []
                for func, arg in commands:
                    if func in self.commands:
                        if self.commands[func][1].get("adminonly", False) and message.nick not in self.admins[
                            message.server]:
                            self.send(message.reply("admin only command: " + func))
                            break
                        else:
                            funcs.append(self.commands[func][0])
                            if self.commands[func][1].get("bufferreplace", True):
                                try:
                                    arg = self.buffer_replace(arg, message.server, message.params)
                                except Exception as e:
                                    self.send(message.reply("error: " + str(e)))
                                    break
                            args.append(message.reply(text=arg))
                    else:
                        self.send(message.reply("unrecognised command: " + func))
                        break
                else:
                    print("commands: ", " ".join(map(str, funcs)))
                    print("args: ", " ".join(map(str, args)))


                    def onError(e):
                        self.send(message.reply(type(e).__name__ + (": " + str(e)) if str(e) else ""))


                    self.worker_pool.apply_async(self.pipe, args=(funcs, args), error_callback=onError)

            self.message_buffer[message.server][message.params].appendleft(message)

        triggered = []
        for plugin in self.plugins.values():
            if message.command == "PRIVMSG":
                for regex, rfunc in plugin._regexes:
                    matches = regex.findall(message.text)
                    for groups in matches:
                        temp = message.copy()
                        temp.groups = groups
                        triggered.append((rfunc, temp))
            for trigger, tfunc in plugin._triggers:
                if trigger(message, bot):
                    triggered.append((tfunc, message))
            for event, efunc in plugin._handlers:
                if message.command.lower() == event.lower():
                    triggered.append((efunc, message))
        self.worker_pool.starmap_async(self.call_trigger, triggered, error_callback=print)

    def call_trigger(self, func, message):
        res = self.resulter()
        next(res)
        func(message, res)

    def send(self, message):
        if message.server in self.servers:
            print(">> " + str(message))
            line = message.to_line()
            if not line.endswith("\n"):
                line += "\n"
            self.servers[message.server].socket.send(line.encode())
            if message.command == "PRIVMSG":
                temp = message.copy()
                temp.nick = self.servers[message.server].nick
                self.message_buffer[message.server][message.params].appendleft(temp)
        else:
            raise Exception("no such server: " + message.server)

    def pipe(self, funcs, args):

        res = self.resulter()
        next(res)

        piped = res
        for func, args in zip(funcs[::-1], args[::-1]):
            piped = func(args, piped)

        piped.send(None)
        piped.close()

    def resulter(self):
        try:
            while 1:
                x = yield
                print("resulter: ", x)
                self.send(x)
        except GeneratorExit:
            pass  # pipe closed


if __name__ == "__main__":
    json_config = codecs.open(argv[1], 'r', 'utf-8-sig')
    config = json.load(json_config)
    bot = PiperBot()

    for plugin_ in config["plugins"]:
        bot.load_plugin_from_module(plugin_)

    for server in config["servers"]:
        server_name = server["IRCNet"]
        network = server["IRCHost"]
        name = server["IRCName"]
        user = server["IRCUser"]
        port = server["IRCPort"]
        nick = server["IRCNick"]
        password = server["IRCPass"] if "IRCPass" in server else None
        autojoin = server["AutoJoin"]
        admins = server["Admins"]
        usessl = server["UseSSL"]
        bot.connect_to(server_name, network, port, nick, autojoin, admins, password, user, name, usessl)
    bot.run()
