from collections import Counter

from wrappers import *
import pymongo


@plugin
class Karma:
    def __init__(self):
        self.karma = Counter()

    @on_load
    def onload(self):
        con = pymongo.MongoClient()
        db = con.karma
        for record in db["karma"].find():
            self.karma[record["key"]] = record["score"]

    @on_unload
    def onunload(self):
        con = pymongo.MongoClient()
        db = con.karma
        for key, score in self.karma.items():
            db.karma.insert({"key": key, "score": score})

    @regex(r"(?:\[([^\[\]]+)\]|(\S+))(\+\+|--)")
    def mod(self, message):
        if message.nick != (message.groups[0] or message.groups[1]):
            self.karma[(message.groups[0] or message.groups[1]).lower()] += {"++": 1, "--": -1}[message.groups[2]]

    @command("karma", simple=True)
    def asd(self, message):
        """shows you your karma or the specified object's karma, karma is gained incrementing or decrementing an object. like so Penguin++"""
        if message.text:
            checked = set()
            for key in message.text.split():
                if key not in checked:
                    checked.add(key)
                    score = self.karma[key.lower()]
                    yield message.reply((key, score), "{} has {} karma!".format(key, score or "no"))
        else:
            key = message.nick
            score = self.karma[key.lower()]
            yield message.reply((key, score), "you have {} karma!".format(score or "no"))


