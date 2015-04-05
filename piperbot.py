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
import sys
import string
import functools
import traceback
from operator import itemgetter

from serverconnection import ServerConnection
from itertools import chain


class User:
    def __init__(self):
        self.channels = defaultdict(list)
        self.data = {}


def _coroutine(func):
    @functools.wraps(func)
    def generator(*args, **kwargs):
        x = func(*args, **kwargs)
        next(x)
        return x
    return generator


class PiperBot(threading.Thread):
    def __init__(self):
        super(PiperBot, self).__init__(daemon=True)

        self.servers = {}

        self.admins = defaultdict(list)
        self.users = defaultdict(lambda: defaultdict(User))
        self.ops = defaultdict(lambda: defaultdict(set))

        self.command_char = "#"
        self.in_queue = PriorityQueue()

        self.apikeys = {}

        self.commands = {}
        self.aliases = {}
        self.plugins = {}

        self.pre_command_exts = []
        self.post_command_exts = []
        self.pre_event_exts = []
        self.post_event_exts = []
        self.pre_trigger_exts = []
        self.post_trigger_exts = []
        self.pre_regex_exts = []
        self.post_regex_exts = []

        self.worker_pool = ThreadPool(processes=8)

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
            else:
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
            else:
                print("command overlap! : " + args["command"])

        for (priority, func) in plugin_instance._command_extensions:
            if priority < 1:
                self.pre_command_exts.append((priority,
                                              plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                              func))
            else:
                self.post_command_exts.append((priority,
                                               plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                               func))
        for (priority, func) in plugin_instance._event_extensions:
            if priority < 1:
                self.pre_event_exts.append((priority,
                                            plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                            func))
            else:
                self.post_event_exts.append((priority,
                                            plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                            func))
        for (priority, func) in plugin_instance._trigger_extensions:
            if priority < 1:
                self.pre_trigger_exts.append((priority,
                                              plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                              func))
            else:
                self.post_trigger_exts.append((priority,
                                               plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                               func))
        for (priority, func) in plugin_instance._regex_extensions:
            if priority < 1:
                self.pre_regex_exts.append((priority,
                                            plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                            func))
            else:
                self.post_regex_exts.append((priority,
                                             plugin_instance.__module__ + "." + plugin_instance.__class__.__name__,
                                             func))

        self.post_command_exts.sort(key=itemgetter(0, 1))
        self.pre_command_exts.sort(key=itemgetter(0, 1))
        self.post_event_exts.sort(key=itemgetter(0, 1))
        self.pre_event_exts.sort(key=itemgetter(0, 1))
        self.post_regex_exts.sort(key=itemgetter(0, 1))
        self.pre_regex_exts.sort(key=itemgetter(0, 1))
        self.post_trigger_exts.sort(key=itemgetter(0, 1))
        self.pre_trigger_exts.sort(key=itemgetter(0, 1))

        if plugin._plugin_thread:
            plugin_instance.start()

    def unload_plugin(self, plugin_name):
        for func, args in self.plugins[plugin_name]._commands:
            if args["command"] in self.commands.keys():
                del self.commands[args["command"]]
        for lump in self.post_command_exts:
            if lump[1] == plugin_name:
                self.post_command_exts.remove(lump)
        for lump in self.pre_command_exts:
            if lump[1] == plugin_name:
                self.pre_command_exts.remove(lump)
        for lump in self.post_event_exts:
            if lump[1] == plugin_name:
                self.post_event_exts.remove(lump)
        for lump in self.pre_event_exts:
            if lump[1] == plugin_name:
                self.pre_event_exts.remove(lump)
        for lump in self.post_regex_exts:
            if lump[1] == plugin_name:
                self.post_regex_exts.remove(lump)
        for lump in self.pre_regex_exts:
            if lump[1] == plugin_name:
                self.pre_regex_exts.remove(lump)
        for lump in self.post_trigger_exts:
            if lump[1] == plugin_name:
                self.post_trigger_exts.remove(lump)
        for lump in self.pre_trigger_exts:
            if lump[1] == plugin_name:
                self.pre_trigger_exts.remove(lump)
        for func in self.plugins[plugin_name]._onUnloads:
            func()
        del self.plugins[plugin_name]

    def handle_message(self, message):
        if message.command == "PING":
            response = message.copy()
            response.command = "PONG"
            self.send(response)
        elif message.command == "PRIVMSG":
            self.message_buffer[message.server][message.params].appendleft(message)

            if message.text.startswith(self.command_char) and message.text[1:]:
                first = message.text[1:].split()[0]
                if first == "alias":
                    self.handle_alias_assign(message)
                elif first in self.commands or first in self.aliases:
                    self.worker_pool.apply_async(self.handle_command,  args=(message,))

        triggered = []
        for plugin in self.plugins.values():
            if message.command == "PRIVMSG":
                for regex, rfunc in plugin._regexes:
                    matches = regex.findall(message.text)
                    for groups in matches:
                        temp = message.copy()
                        temp.groups = groups
                        triggered.append((rfunc, temp, self.pre_regex_exts, self.post_trigger_exts))
            for trigger, tfunc in plugin._triggers:
                if trigger(message, bot):
                    triggered.append((tfunc, message, self.pre_trigger_exts, self.post_trigger_exts))
            for event, efunc in plugin._handlers:
                if message.command.lower() == event.lower():
                    triggered.append((efunc, message, self.pre_event_exts, self.post_event_exts))
        self.worker_pool.starmap_async(self.call_triggered, triggered, error_callback=print)

    def call_triggered(self, func, message, pre=[], post=[]):
        try:
            pipe = self.resulter()

            for _, _, func_, in post:
                    pipe = func_(message, pipe)

            pipe = func(pipe)
            next(pipe)
            for _, _, func_ in pre:
                pipe = func_(message, pipe)

            pipe.send(message)
        except StopIteration as e:
            raise e
        except Exception as e:
            print("Error calling trigger: %s : %s: %s" % (func.__name__, type(e), e))

    def handle_alias_assign(self, message):
        try:
            name, *alias = message.text[len(self.command_char)+5:].split("=")
            name = name.strip()
            alias = "=".join(alias).strip()
            if name in self.commands:
                raise Exception("cannot overwrite existing command")

            commands = map(lambda x: [(command, " ".join(args)) for command, *args in [x.split(" ")]][0],
                           map(lambda x: x.strip(), alias.split(" || ")))
            funcs = []
            args = []
            for func, arg in commands:
                if func in self.commands:
                        funcs.append(self.commands[func][1]["command"])
                        args.append(arg)
                elif func in self.aliases:
                    if func == name:
                        raise Exception("recursion detected")
                    funcs_, args_ = self.aliases[func]
                    funcs.extend(funcs_)
                    args.extend(args_)
                else:
                    raise Exception("unrecognised command: " + func)

            self.aliases[name] = list(zip(funcs, args))

            self.send(message.reply("The alias %s has been saved" % name))
        except Exception as e:
            self.send(message.reply(type(e).__name__ + (": " + str(e)) if str(e) else ""))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("*** print_tb:")
            traceback.print_tb(exc_traceback, file=sys.stdout)




    def handle_command(self, message):
        try:
            def prepper(results):
                while 1:
                    x = yield
                    results.append(x)

            results = []

            prepipe = prepper(results)
            next(prepipe)

            for _, _, f in self.pre_command_exts:
                prepipe = f(message, prepipe)
            prepipe.send(message)

            for result in results:

                while "$(" in result.text:
                    result = self.handle_inners(result)

                funcs, args = self.funcs_n_args(result)

                pipe = self.resulter()

                for func, args in chain([(f, message) for _, _, f in self.post_command_exts],
                                        list(zip(funcs[::-1], args[::-1]))):
                    pipe = func(args, pipe)

                pipe.send(None)
                pipe.close()
        except Exception as e:
            self.send(message.reply(type(e).__name__ + (": " + str(e)) if str(e) else ""))
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("*** print_tb:")
            traceback.print_tb(exc_traceback, file=sys.stdout)


    def funcs_n_args(self, message):
        commands = map(lambda x: [(command, " ".join(args)) for command, *args in [x.split(" ")]][0],
                       map(lambda x: x.strip(), message.text[1:].split(" || ")))
        funcs = []
        args = []
        for i, (func, arg) in enumerate(commands):
            if func in self.commands:
                if self.commands[func][1].get("adminonly", False) and message.nick not in self.admins[message.server]:
                    raise Exception("admin only command: " + func)
                else:
                    funcs.append(self.commands[func][0])
                    if self.commands[func][1].get("bufferreplace", True):
                        arg = self.buffer_replace(arg, message.server, message.params, offset=1)
                    temp = message.reply(arg)

                    if self.commands[func][1].get("argparse", False):
                        text, args_ = self.parse_args(temp, self.commands[func][0], func)

                        temp = message.reply(text)
                        temp.args = args_

                    args.append(temp)
            elif func in self.aliases:

                funcs.append(self.argpass)
                args.append(message.reply(arg))


                for func_, arg_ in self.aliases[func]:
                    if self.commands[func_][1].get("adminonly", False) \
                            and message.nick not in self.admins[message.server]:
                        raise Exception("admin only command: " + func)
                    else:
                        funcs.append(self.commands[func_][0])
                        if self.commands[func_][1].get("bufferreplace", True):
                            arg__ = self.buffer_replace(arg_, message.server, message.params, offset=1)
                        else:
                            arg__ = arg_
                        temp = message.reply(arg__)


                        if self.commands[func_][1].get("argparse", True):
                            text, args_ = self.parse_args(temp, self.commands[func_][0], func_)

                            temp = message.reply(text)
                            temp.args = args_

                        args.append(temp)
            else:
                raise Exception("unrecognised command: " + func)

        return funcs, args

    def parse_args(self, message, func, funcname):
        if hasattr(func, "_args"):
            args = dict(func._args)
        else:
            args = {}

        if message.text.startswith('"') and message.text.endswith('"'):
            return message.data[1:-1], args

        words = message.data.split()
        msg = []

        for word in words:
            if word.startswith("--"):
                word = word[2:]
                if "=" in word:
                    arg, _, value = word.partition("=")
                    if arg not in args:
                        raise Exception("invalid argument: %s for command %s" % (arg, funcname))
                    values = {
                        "True": True,
                        "False": False,
                    }
                    if value in values:
                        value = values[value]


                    args[arg] = value
                else:
                    if word not in args:
                        raise Exception("invalid argument: %s for command %s" % (word, funcname))
                    args[word] = True
            elif word.startswith("-"):
                word = word[1:]
                for flag in word:
                    if flag not in args:
                        raise Exception("invalid flag: %s for command %s" % (flag, funcname))
            else:
                msg.append(word)

        return " ".join(msg), args


    def handle_inners(self, message):
        first = message.text.find("$(")

        left = message.text[:first]
        rest = message.text[first+1:]
        openbr = 0
        prevchar = ""
        for i, char in enumerate(rest):
            if prevchar+char == "$(":
                openbr += 1
            if char == "$" and prevchar == ")":
                if openbr != 0:
                    openbr -= 1
                else:
                    final = i
                    break
            prevchar = char
        else:
            raise Exception("no closing bracket")

        middle = rest[:final-1]
        right = rest[final+1:]

        while "$(" in middle:
            middle = self.handle_inners(message.reply(middle)).text

        funcs, args = self.funcs_n_args(message.reply(middle))
        text = []
        cat = self.concater(text)
        pipe = cat
        for func, args in zip(funcs[::-1], args[::-1]):
            pipe = func(args, pipe)

        pipe.send(None)
        pipe.close()

        return message.reply(text=left + " ".join(text) + right)

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


    @_coroutine
    def argpass(self, arg, target):
        formats = len(list(string.Formatter().parse(arg.text)))
        try:
            while 1:
                x = yield
                if x is None:
                    if not arg.data:
                        target.send(None)
                    else:
                        if formats:
                            target.send(arg.reply(data=arg.data.format(*([""] * formats)), args=arg.args))
                        else:
                            target.send(arg)
                else:
                    if formats:
                        if x.data is not None:
                            target.send(x.reply(data=arg.data.format(*([x.data] * formats)), args=arg.args))
                        else:
                            target.send(x.reply(data=arg.data.format(*([""] * formats)), args=arg.args))
                    else:
                        target.send(x.reply(data=x.data, args=arg.args))
        except GeneratorExit:
            target.close()

    @_coroutine
    def resulter(self):
        try:
            while 1:
                x = yield
                self.send(x)
        except GeneratorExit:
            pass  # pipe closed

    @_coroutine
    def concater(self, results):
        try:
            while 1:
                x = yield
                results.append(x.data)
        except GeneratorExit:
            pass  # pipe closed








if __name__ == "__main__":
    json_config = codecs.open(argv[1], 'r', 'utf-8-sig')
    config = json.load(json_config)
    bot = PiperBot()

    if "apikeys" in config:
        for api, key in config["apikeys"]:
            bot.apikeys[api] = key

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
