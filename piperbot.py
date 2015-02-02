import re
import copy
from collections import defaultdict, deque
import threading
from concurrent import futures
from multiprocessing import Manager
from queue import PriorityQueue, Empty
import inspect
from serverconnection import ServerConnection
from Message import RawLine
import importlib
import imp
import os
import sys
import traceback


class PiperBot(threading.Thread):
    def __init__(self):
        super(PiperBot, self).__init__(daemon=True)
        
        self.servers = {}
        
        self.admins = defaultdict(list)
        
        self.command_char = "#"
        
        self.in_queue = PriorityQueue()

        self.commands = {}
        self.plugins = {}
        
        self.dispatcher_pool = futures.ThreadPoolExecutor(4)
        self.worker_pool = futures.ThreadPoolExecutor(4)
        
        self.manager = Manager() 

        self.message_buffer = defaultdict(lambda: defaultdict(lambda:deque(maxlen=20)))
        
        self.buffer_pattern = re.compile(r"(?:(\w+)|\s)(?:\^(\d+)|(\^+))")
        self.escaped_buffer_pattern = re.compile(r"\\\^")
        
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
                print(message)
                self.dispatcher_pool.submit(self.handle_message, message)
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
            temp = imp.load_source(module, os.path.dirname(os.path.abspath(__file__))+"/plugins/"+module+".py")
            found = False
            for name, Class in inspect.getmembers(temp, lambda x: inspect.isclass(x) and hasattr(x, "_plugin")):
                if name == plugin_name:
                    self.load_plugin(Class)
                    found = True
            if not found:
                raise Exception("no such plugin to load")
        else:
            temp = imp.load_source(plugin, os.path.dirname(os.path.abspath(__file__))+"/plugins/"+plugin+".py")
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
            print(plugin_name)
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
            self.servers[response.server].out_queue.put(response)

        responses = self.manager.Queue()
        trigger_count = 0
        
        if message.command == "PRIVMSG" and message.text.startswith(self.command_char):
            temp = message.copy()
            try:
                temp.text = self.buffer_pattern.sub(lambda x: self.buffer_replace(self.message_buffer[message.server][message.params], x), message.text[len(self.command_char):])
                temp.text = self.escaped_buffer_pattern.sub("^", temp.text)
            except Exception as e:
                    print(traceback.print_exc(file=sys.stdout))
                    trigger_count += 1
                    responses.put("error: " + str(e))
                    responses.put("END")
                
            splits = list(map(lambda x: x.strip(),temp.text.split(" | ")))
            funcs = []
            args = []
            valid = False
            if splits and splits[0].split()[0].strip() and splits[0].split()[0].strip() in self.commands:
                command = splits[0].split()[0].strip() 
                if self.commands[command][1].get("adminonly", False) and message.nick not in self.admins[message.server]:
                    valid = False
                    temp.text = "admin only command"
                    trigger_count += 1
                    responses.put(temp)
                    responses.put("END")
                else:
                    valid = True
                    funcs.append(self.commands[splits[0].split()[0]][0])
                    initial = " ".join(splits[0].split()[1:]) 
                    temp.text = initial
            for segment in splits[1:]:
                command = segment.split()[0]
                if command not in self.commands:
                    valid = False
                    temp.text = "unrecognised command: " + command
                    trigger_count += 1
                    responses.put(temp)
                    responses.put("END")
                    break
                elif not self.commands[command][1].get("pipeable", True) and segment != splits[-1]:
                    valid = False
                    temp.text = "unpipeable command: " + command
                    trigger_count += 1
                    responses.put(temp)
                    responses.put("END")
                    break
                elif self.commands[command][1].get("adminonly", False) and message.nick not in self.admins[message.server]:
                    valid = False
                    temp.text = "admin only command: " + command
                    trigger_count += 1
                    responses.put(temp)
                    responses.put("END")
                    break
                else:
                    funcs.append(self.commands[command][0])
                if len(segment.split()) > 1:
                    args.append(" ".join(segment.split()[1:])+" ")
                else:
                    args.append("")
            args.append("")
            if valid:
                trigger_count += 1
                self.worker_pool.submit(handle_responses, self.pipe, responses, temp, funcs, args)
        
        if message.command == "PRIVMSG":
            self.message_buffer[message.server][message.params].appendleft(message)
        
        for plugin in self.plugins.values():
            if message.command == "PRIVMSG":
                for regex, func in plugin._regexes:
                    match = regex.match(message.text)
                    if match:
                        trigger_count += 1
                        message.groups = match.groups()
                        self.worker_pool.submit(handle_responses,func,responses,message)
            for trigger, func in plugin._triggers:
                if trigger(message,bot):
                    trigger_count += 1
                    self.worker_pool.submit(handle_responses, func, responses, message)
        end_count = 0
        while end_count != trigger_count:
            response = responses.get()
            if response == "END":
                end_count += 1
            else:
                if response.command == "PRIVMSG":
                    tempmessage = response.copy()
                    tempmessage.nick = self.servers[tempmessage.server].nick
                    self.message_buffer[tempmessage.server][tempmessage.params].appendleft(tempmessage)
                self.send(response)
                
    def send(self, message):
        if message.server in self.servers:
            self.servers[message.server].out_queue.put(message)
        else:
            raise Exception("no such server")
                
    def pipe(self, initial, funcs, args):
        if len(funcs) == 1:
            for x in funcs[0](initial):
                temp = x.copy()
                temp.text = args[0] + temp.text
                yield temp
        else:
            for y in self.pipe(initial, funcs[:-1], args[:-1]):
                for x in funcs[-1](y):
                    temp = x.copy()
                    temp.text = args[-1] + temp.text
                    yield temp


def handle_responses(callable_, queue, *args):
    try:
        x = callable_(*args)
        if inspect.isgenerator(x):
            for i in x:
                queue.put(i)
        elif x:
            queue.put(x)
    except Exception as e:
        error_response = args[0].get_reply()
        error_response.text = "error: " + str(e)
        queue.put(error_response)
    finally:
        queue.put("END")

if __name__=="__main__":
    #server 1
    server_name = "UKC"
    network = 'irc.compsoc.kent.ac.uk'
    port = 6697
    nick = 'PiperBot2'
    channels = ['#bottesting']
    admins = ["Penguin"]
    #server 2
    server_name2 = "freenode"
    network2 = "holmes.freenode.net"
    port2 = 6667
    nick2 = "PiperBot"
    channels2 = ["#KentCS","#piperbot"]
    admins2 = ["Pengwin"]
    
    bot = PiperBot()
    #bot.connect_to(server_name, network, port, nick, channels, admins, password="wassak12!", username="ec344", ssl=True)
    bot.connect_to(server_name2, network2, port2, nick2, channels2, admins2)
    bot.load_plugin_from_module("general")
    # bot.load_plugin_from_module("testing.testing1")
    # bot.load_plugin_from_module("testing.testing2")
    bot.load_plugin_from_module("admintools")
    bot.load_plugin_from_module("translate")
    bot.load_plugin_from_module("markov")
    bot.run()
