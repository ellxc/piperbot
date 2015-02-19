import re
from collections import defaultdict, deque
import threading
from multiprocessing.pool import ThreadPool
from queue import PriorityQueue, Empty
import inspect
from serverconnection import ServerConnection
import importlib
import os
import string
import json
import codecs
from sys import argv

class PiperBot(threading.Thread):
    def __init__(self):
        super(PiperBot, self).__init__(daemon=True)
        
        self.servers = {}
        
        self.admins = defaultdict(list)
        
        self.command_char = "#"
        self.in_queue = PriorityQueue()

        self.commands = {}
        self.plugins = {}

        self.worker_pool = ThreadPool(processes=4)

        self.message_buffer = defaultdict(lambda: defaultdict(lambda:deque(maxlen=50)))
        self.buffer_pattern = re.compile(r"(?:(\w+)|\s)(?:\^(\d+)|(\^+))")
        self.escaped_buffer_pattern = re.compile(r"\\\^")
        
        self.stringformatter = string.Formatter()
        
        self.running = False
        
    def buffer_replace(self, buffer, match_object):
        if match_object.group(1):
            buffer = [x for x in list(buffer) if x.nick == match_object.group(1)]
            if not buffer:
                raise Exception("user not in memory")
        if match_object.group(2):
            count = int(match_object.group(2))
        elif match_object.group(3):
            count = len(match_object.group(3))
        if count <= len(buffer):
            return " "+buffer[count-1].text
        else:
            raise Exception("line not in memory")
        
    def connect_to(self, servername, network, port, nick, channels=None, admins=None, password=None, username=None, ircname = None, ssl=False):
        self.servers[servername] = ServerConnection(self.in_queue, servername, network, port, nick, password, username, ircname, channels,ssl )
        self.servers[servername].connect()
        if admins:
            self.admins[servername] += admins

    def run(self):
        self.running = True
        while self.running:
            try:
                message = self.in_queue.get(timeout=10)
                print("<< " + str(message))
                self.handle_message(message)
            except Empty:
                pass
                
    def shutdown(self):
        self.running = False
        for plugin_name in self.plugins.keys():
            self.unload_plugin(plugin_name)

    def load_plugin_from_module(self, plugin):
        if "." in plugin:
            module = "".join(plugin.split(".")[:-1])
            plugin_name = plugin.split(".")[-1]
            temp = importlib.machinery.SourceFileLoader(module, os.path.dirname(os.path.abspath(__file__))+"/plugins/"+module+".py").load_module()
            print(temp)
            found = False
            for name, Class in inspect.getmembers(temp, lambda x: inspect.isclass(x) and hasattr(x, "_plugin")):
                if name == plugin_name:
                    self.load_plugin(Class)
                    found = True
            if not found:
                raise Exception("no such plugin to load")
        else:
            temp = importlib.machinery.SourceFileLoader(plugin, os.path.dirname(os.path.abspath(__file__))+"/plugins/"+plugin+".py").load_module()
            print()
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
        if plugin.__module__+"."+plugin.__name__ in self.plugins:
            raise Exception("already loaded!")
        plugin_instance = plugin()
        plugin_instance._plugin__init__(self)
        for func in plugin_instance._onLoads:
            func()
        self.plugins[plugin_instance.__module__+"."+plugin_instance.__class__.__name__] = plugin_instance
        for (func, args) in plugin_instance._commands:
            if args["command"] not in self.commands:
                self.commands[args["command"]] = (func, args)
            else:
                print("command overlap! : " + args["command"])
                
    def unload_plugin(self, plugin_name):
        for func,args in self.plugins[plugin_name]._commands:
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
            if message.text.startswith(self.command_char):
                temp = message.copy()
                try:
                    temp.text = self.buffer_pattern.sub(lambda x: self.buffer_replace(self.message_buffer[message.server][message.params], x), message.text[len(self.command_char):])
                    temp.text = self.escaped_buffer_pattern.sub("^", temp.text)
                except Exception as e:
                        self.send(message.reply("error: " + str(e)))

                splits = list(map(lambda x: x.strip(),temp.text.split(" || ")))
                funcs = []
                args = []
                valid = False
                if splits and splits[0].split()[0].strip() and splits[0].split()[0].strip() in self.commands:
                    command = splits[0].split()[0].strip()
                    if self.commands[command][1].get("adminonly", False) and message.nick not in self.admins[message.server]:
                        valid = False
                        self.send(message.reply("admin only command: " +command))
                    else:
                        valid = True
                        funcs.append(self.commands[splits[0].split()[0]][0])
                        initial = " ".join(splits[0].split()[1:])
                for segment in splits[1:]:
                    command = segment.split()[0]
                    if command not in self.commands:
                        valid = False
                        self.send(message.reply("unrecognised command: " + command))
                        break
                    elif not self.commands[command][1].get("pipeable", True) and segment != splits[-1]:
                        valid = False
                        self.send(message.reply("unpipeable command: " + command))
                        break
                    elif self.commands[command][1].get("adminonly", False) and message.nick not in self.admins[message.server]:
                        valid = False
                        self.send(message.reply("admin only command: " +command))
                        break
                    else:
                        funcs.append(self.commands[command][0])
                    if len(segment.split()) > 1:
                        args.append(" ".join(segment.split()[1:])+" ")
                    else:
                        args.append("")
                args.append("")
                if valid:
                    self.worker_pool.apply_async(lambda msg,funcs_,args_: self.handle_responses(self.pipe(msg,funcs_,args_),initial=message), args=(temp.reply(initial), funcs, args),error_callback=lambda e: self.send(message.reply("error: " + str(e))))

            self.message_buffer[message.server][message.params].appendleft(message)

        triggered = []
        for plugin in self.plugins.values():
            if message.command == "PRIVMSG":
                for regex, rfunc in plugin._regexes:
                    match = regex.match(message.text)
                    if match:
                        triggered.append(rfunc)
            for trigger, tfunc in plugin._triggers:
                if trigger(message, bot):
                    triggered.append(tfunc)
            for event, efunc in plugin._handlers:
                if message.command.lower() == event.lower():
                    triggered.append(efunc)

        self.worker_pool.map_async(lambda x: self.handle_responses(x(message)), triggered, error_callback=lambda e: print("error: " + str(e)))

    def send(self, message):
        if message.server in self.servers:
            print(">> " + str(message))
            line = message.to_line()
            if not line.endswith("\n"):
                line += "\n"
            self.servers[message.server].socket.send(line.encode())
            if message.command == "PRIVMSG":
                self.message_buffer[message.server][message.params].appendleft(message)
        else:
            raise Exception("no such server: " + message.server)
                
    def pipe(self, initial, funcs, args):
        if len(funcs) == 1:
            for x in funcs[0](initial):
                temp = x.copy()
                if args[0]:
                    formats = list(self.stringformatter.parse(args[0]))

                    if len(formats) > 1 or (formats and any(map(lambda x: x is not None,formats[0][1:]))):
                        temp.text = args[0].format(*([temp.text]*len(formats)))
                    else:
                        temp.text = args[0] + temp.text
                yield temp
        else:
            for y in self.pipe(initial, funcs[:-1], args[:-1]):
                for x in funcs[-1](y):
                    temp = x.copy()
                    
                    formats = list(self.stringformatter.parse(args[-1]))
                
                    if len(formats) > 1 or (formats and any(map(lambda x: x is not None,formats[0][1:]))):
                        temp.text = args[-1].format(*([temp.text]*len(formats)))
                    else:
                        temp.text = args[-1] + temp.text

                    yield temp

    def handle_responses(self, response, initial=None):
        if response:
            try:
                if inspect.isgenerator(response):
                    for i in response:
                        self.send(i)
                else:
                    self.send(response)
            except Exception as e:
                if initial is not None:
                    self.send(initial.reply(type(e).__name__ + (": " + str(e)) if str(e) else ""))
                print(e)

if __name__=="__main__":
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
