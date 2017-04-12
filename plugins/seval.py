import ast
from wrappers import *
from plugins.stuff.seval import seval
from collections import defaultdict, Counter, namedtuple
import math
import datetime
import json
import random
import sys
import traceback
import pytz
from functools import partial
import dateutil.parser
from Namespaces import *
import pickle
import unicodedata
import itertools
from base64 import b64encode, b64decode

@plugin
class Eval:
    @on_load
    def init(self):
        try:
            self.userspaces = pickle.load(open("sevaluserspaces.pickle", "rb"))
        except FileNotFoundError:
            pass

    @on_unload
    def save(self):
        pickle.dump(self.userspaces, open("sevaluserspaces.pickle", "wb"))


    def __init__(self):
        self.localenv = {}

        self.userspaces = {}


    @adv_command(">", bufferreplace=False, argparse=False)
    @adv_command("seval", bufferreplace=False, argeparse=False)
    def calc(self, arg, target):
        """oh boy, so this is a python interpreter, you can do most things you could do from a terminal, but only single line statements are allowed. you can chain multiple single statements together using ';' and you can access any piped in message via 'message'"""


        try:
            while 1:
                message = yield
                if message is None:
                    message = arg


                todelete = set(self.localenv.keys())
                selftodelete = set(self.userspaces.setdefault(message.server, {}).setdefault(message.nick, {}).keys())

                responses, env, self_ = timed(sevalcall, args=(arg.text.strip(), self.localenv, self.userspaces, message))

                if isinstance(responses, list):
                    for response in responses:
                        target.send(arg.reply(response, repr(response)))
                elif isinstance(responses, SyntaxError):
                    raise responses

                for key, item in env.items():
                    self.localenv[key] = item
                    if key in todelete:
                        todelete.remove(key)

                for key in todelete:
                    del self.localenv[key]

                for key, item in self_.items():
                    self.userspaces[arg.server][arg.nick].update(**{key: item})
                    if key in selftodelete:
                        selftodelete.remove(key)

                for key in selftodelete:
                    del self.userspaces[arg.server][arg.nick][key]

                if isinstance(responses, Exception):
                    raise responses

        except GeneratorExit:
            target.close()

    @adv_command("filter", bufferreplace=False, argeparse=False)
    def filt(self, arg, target):
        try:
            while 1:
                message = yield
                if message is None:
                    pass
                else:
                    response, *_ = timed(sevalcall, args=(arg.text.strip(), self.localenv, self.userspaces, message))
                    if response and response[-1]:
                        target.send(message)


        except GeneratorExit:
            target.close()

    @command("liteval", bufferreplace=False, argeparse=False)
    def liteval(self, message):
        'will evaluate python literals. pretty simple version of seval'
        result = ast.literal_eval(message.text.strip())
        return message.reply(result, repr(result))


def raise_(text=None):
    raise Exception(text)


b64 = namedtuple('base64', ('b64encode', 'b64decode'))(b64encode, b64decode)

globalenv = {
    "itertools":itertools,
    "abs": abs,
    "all": all,
    "any": any,
    "ascii": ascii,
    "bin": bin,
    "bool": bool,
    "callable": callable,
    "chr": chr,
    "complex": complex,
    "dict": dict,
    "dir": dir,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "hasattr": hasattr,
    "hash": hash,
    "hex": hex,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "int": int,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "Counter":Counter,
    "json":json,
    "sin": math.sin,
    "pi": math.pi,
    "math": math,
    "random": random,
    "datetime": datetime.datetime,
    "date": datetime.date,
    "time": datetime.time,
    "timedelta": datetime.timedelta,
    "timestamp": datetime.datetime.fromtimestamp,
    "re": re,
    "pytz": pytz,
    "dateparse": dateutil.parser.parse,
    "raise_": raise_,
    "Exception": Exception,
    "unicodedata":unicodedata,
    "base64":b64,
}


def sevalcall(text, localenv, userspaces, message):
    ret = {}
    retenv = localenv.copy()
    try:
        env = localenv.copy()



        for user, userenv in userspaces[message.server].items():
            env.update(**{user: ReadOnlyNameSpace(userenv, all=True)})

        env.update(servers=ReadOnlyNameSpace(userspaces, all=True))
        env.update(users=ReadOnlyNameSpace(userspaces[message.server], all=True))
        env.update(self=MutableNameSpace(userspaces[message.server][message.nick], all=True))

        env.update(globalenv)

        env.update(message=message)
        env.update(seval=seval_)
        #env.update(env=env)

        responses, retenv = seval(text, env)


        for key, item in retenv.items():
            if key not in globalenv and key not in ["self", "users", "servers", "seval", "message"]:
                ret[key] = item
        return responses, ret, retenv.setdefault("self", {})
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("*** print_tb:")
        traceback.print_tb(exc_traceback, file=sys.stdout)
        return e, ret, retenv.setdefault("self", {})

def seval_(text, env={}):
    tempenv = dict(globalenv)
    tempenv.update(env)
    tempenv.update(seval=seval_)
    return seval(text, tempenv)[0]
