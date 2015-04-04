from collections import Counter

from wrappers import *
import json


@plugin
class Karma:
    def __init__(self):
        self.karma = Counter()

    @on_load
    def onload(self):
        with open('karma.json', 'r') as infile:
            aliases = json.load(infile)
            for name, score in aliases.items():
                self.karma[name] = score

    @on_unload
    def onunload(self):
        with open('karma.json', 'w') as outfile:
            json.dump(self.karma, outfile, sort_keys=True, indent=4, ensure_ascii=False)

    @regex(r"(?:\[([^\[\]]+)\]|(\S+))(\+\+|--)")
    def mod(self, message):
        if message.nick != (message.groups[0] or message.groups[1]):
            self.karma[(message.groups[0] or message.groups[1]).lower()] += {"++": 1, "--": -1}[message.groups[2]]

    @command("karma", simple=True)
    def asd(self, message):
        """shows you your karma or the specified object's karma, karma is gained incrementing or decrementing an object. like so Penguin++"""
        if message.data:
            if isinstance(message.data, str):
                checked = set()
                results = []
                for key in message.text.split():
                    if key not in checked:
                        checked.add(key)
                        score = self.karma[key.lower()]
                        results.append((key, score))

                if len(results) == 1:
                    text = "{} has {} karma!".format(results[0][0], results[0][1] or "no")
                else:
                    text = ", ".join(["%s: %s" % (x, score) for (x, score) in results])
                yield message.reply(data=results, text=text)


            else:
                checked = set()
                results = []
                for x in iter(message.data):
                    assert isinstance(x, str), TypeError("expected str, got %s" % type(x))
                    if x not in checked:
                        checked.add(x)
                        score = self.karma[x.lower()]
                        results.append((x, score))
                text = ", ".join(["%s: %s" % (x, score) for (x, score) in results])
                yield message.reply(data=results, text=text)


        else:
            key = message.nick
            score = self.karma[key.lower()]
            yield message.reply([(key, score)], "you have {} karma!".format(score or "no"))


