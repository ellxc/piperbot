from threading import Thread, Event
import datetime

from wrappers import *
from Message import Message
from dateutil import parser
import pymongo
import dill


@plugin(thread=True)
class Reminders(Thread):
    def __init__(self):
        super(Reminders, self).__init__()
        self.reminders = []
        self.event = Event()
        self.ticking = False

    @on_load
    def init(self):
        con = pymongo.MongoClient()
        db = con["reminders"]
        for reminder_ in db["reminders"].find():
            self.reminders.append(dill.loads(reminder_["reminder"]))
        self.reminders.sort()
        db.reminders.remove({})

    @on_unload
    def stop(self):
        self.ticking = False
        self.event.set()
        con = pymongo.MongoClient()
        db = con["reminders"]
        for reminder in self.reminders:
            db["reminders"].insert({"reminder": dill.dumps(reminder)})

    @command("date")
    def parse(self, message):
        if message.text:
            date = parser.parse(message.text)
        else:
            date = datetime.datetime.now()
        #date = datetime_(date.year,date.month,date.day,date.hour,date.minute,date.second,date.microsecond,date.tzinfo)
        return message.reply(text=str(date), data=date)

    @command
    def reminders(self, message):
        reminders = []
        for reminder_ in self.reminders:
            if message.nick == reminder_.set_for:
                reminders.append(reminder_)
        text = "you have %s reminders! %s"
        count = len(reminders)
        if count < 3 or message.params[0] is not "#":
            text3 = " and ".join([", ".join(reminders[:1])] or [] + [reminders[0:1]])
            text2 = " they are: %".format(text3)
        else:
            text2 = "you have too many to post here, private message me for the list"

        text = text.format(count, text2)
        return message.reply(text=text)

    @command
    def remind(self, message):
        if message.data:
            if isinstance(message.data, datetime.datetime):
                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               message.data, message._text or "", message.params,
                                               message.server))
                self.reminders.sort()
                self.event.set()
                return message.reply("reminder set for %s!" % str(message.data))
            elif isinstance(message.data, datetime.timedelta):
                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               datetime.datetime.today() + message.data, message._text or "", message.params,
                                               message.server))
                self.reminders.sort()
                self.event.set()
                return message.reply("reminder set to go in %s!" % str(message.data))
            else:
                raise TypeError("expected a datetime or timedelta object")
        else:
            if message.text.startswith("in"):
                return message.reply(text="not implemented yet...")
            elif message.text.startswith("at"):
                date, *msg = message.text[3:].split("to")
                date = parser.parse(date)
                msg = "to".join(msg)
                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               date, msg or "", message.params,
                                               message.server))
                self.reminders.sort()
                self.event.set()
                return message.reply("reminder set for %s!" % str(message.data))
            else:


                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               datetime.datetime.today() + datetime.timedelta(0, 10), "",
                                               message.params,
                                               message.server))
                self.reminders.sort()
                self.event.set()
                return message.reply("10 second reminder set!")

    def run(self):
        self.ticking = True
        while self.ticking:
            if self.reminders and self.reminders[0].due_time <= datetime.datetime.today():
                self.bot.send(self.reminders[0].to_message())
                del self.reminders[0]
            else:
                if self.reminders:
                    self.event.wait((self.reminders[0].due_time - datetime.datetime.today()).total_seconds())
                else:
                    self.event.wait()
                self.event.clear()


class reminder:
    def __init__(self, set_by, set_for, set_time, due_time, message, channel, server):
        self.set_by = set_by
        self.set_for = set_for
        self.set_time = set_time
        self.due_time = due_time
        self.message = message
        self.channel = channel
        self.server = server

    def to_message(self):
        text = self.set_for + ": "
        if self.set_by == self.set_for:
            text += "reminder"
        else:
            text += self.set_by + " reminds you"
        if self.message:
            text += ": " + self.message
        else:
            text += "!"
        return Message(server=self.server, command="PRIVMSG", params=self.channel, text=text)

    def __lt__(self, other):
        try:
            return other.due_time > self.due_time
        except:
            pass
        return 0