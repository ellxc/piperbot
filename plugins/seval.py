import ast
from wrappers import *
from plugins.stuff.seval import seval

import math
import datetime
import json
import random
import sys

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
                    response, _ = timed(sevalcall, args=(arg.text.strip(), self.localenv, message))

                    if response:
                        target.send(message)


        except GeneratorExit:
            target.close()

    @command("liteval", bufferreplace=False, argeparse=False)
    def liteval(self, message):
        'will evaluate python literals. pretty simple version of seval'
        result = ast.literal_eval(message.text.strip())
        return message.reply(result, repr(result))


def sevalcall(text, localenv, message):
    env = localenv.copy()

    globalenv = {
    "maxint": sys.maxsize,
    'len': len,
    'hex': hex,
    'map': map,
    'range': range,
    'str': str,
    "int": int,
    "float": float,
    "dict": dict,
    "set": set,
    "sorted":sorted,
    "json":json,
    'zip': zip,
    'list': list,
    'bool': bool,
    "sin": math.sin,
    "pi": math.pi,
    "math": math,
    "ord": ord,
    "chr": chr,
    "random": random,
    "datetime": datetime.datetime,
    "date": datetime.date,
    "time": datetime.time,
    "timedelta": datetime.timedelta,
    "timestamp": datetime.datetime.fromtimestamp,
    "message": message,
    "re": re,
    }

    env.update(globalenv)

    responses = seval(text, env)

    for key, item in env.items():
        if key not in globalenv:
            localenv[key] = item

    return responses, localenv