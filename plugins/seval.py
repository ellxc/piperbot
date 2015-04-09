import ast
from wrappers import *
from plugins.stuff.seval import seval
from collections import defaultdict
import math
import datetime
import json
import random
import sys
import pytz

@plugin
class Eval:
        # #@on_load
        # def init(self):
        #     con = pymongo.MongoClient()
        #     db = con["seval"]
        #     for table in db.collection_names():
        #         for record in db[table].find({"bin": {"$exists": True}}):
        #             userenv[table][record["key"]] = pickle.loads(record["bin"])
        #
        # #@on_unload
        # def save(self):
        #     con = pymongo.MongoClient()
        #     db = con["seval"]
        #     for user, space in userenv.items():
        #         for key, val in space.items():
        #             db[user].insert({"key": key, "bin": pickle.dumps(val)})

    def __init__(self):
        self.localenv = {}
       # self.userspaces = de


    @adv_command(">", bufferreplace=False, argparse=False)
    @adv_command("seval", bufferreplace=False, argeparse=False)
    def calc(self, arg, target):
        """oh boy, so this is a python interpreter, you can do most things you could do from a terminal, but only single line statements are allowed. you can chain multiple single statements together using ';' and you can access any piped in message via 'message'"""


        try:
            while 1:
                message = yield
                if message is None:
                    message = arg

                responses, env = timed(sevalcall, args=(arg.text.strip(), self.localenv, message))

                for response in responses:
                    target.send(arg.reply(response, repr(response)))

                for key, item in env.items():
                    self.localenv[key] = item

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
                    response, *_ = timed(sevalcall, args=(arg.text.strip(), self.localenv, message))
                    print(response)
                    if response and response[-1]:
                        target.send(message)


        except GeneratorExit:
            target.close()

    @command("liteval", bufferreplace=False, argeparse=False)
    def liteval(self, message):
        'will evaluate python literals. pretty simple version of seval'
        result = ast.literal_eval(message.text.strip())
        return message.reply(result, repr(result))


class userspace(dict):
     def __init__(self, *args, **kwargs):
         super(userspace, self).__init__(*args, **kwargs)

     def __getattr__(self, name):
         if name not in self:
             if name.startswith("__"):
                 return dict.__getattribute__(self, name)
             else:
                 self[name] = userspace()
         return self[name]

     def __setattr__(self, key, value):
         self[key] = value


globalenv = {
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
}

def sevalcall(text, localenv, message):
    env = localenv.copy()

   # env.update(userspaces)



    env.update(globalenv)

    env.update(message=message)

    responses = seval(text, env)

    for key, item in env.items():
        if key not in globalenv:
            localenv[key] = item

    return responses, localenv#, self