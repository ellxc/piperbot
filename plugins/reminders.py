from threading import Thread, Event
import datetime

from wrappers import *
from Message import Message


@plugin(thread=True)
class Reminders(Thread):
    def __init__(self):
        super(Reminders, self).__init__()
        self.reminders = []
        self.event = Event()
        self.ticking = False

    @on_unload
    def stop(self):
        self.ticking = False
        self.event.set()

    @command(pipable=False)
    def remind(self, message):
        if message.data:
            if isinstance(message.data, datetime.datetime):
                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               message.data, message.text, message.params,
                                               message.server))
                yield message.reply("reminder set for %s!" % str(message.data))
            elif isinstance(message.data, datetime.timedelta):
                self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                               datetime.datetime.today() + message.data, message.text, message.params,
                                               message.server))
                yield message.reply("reminder set to go in %s!" % str(message.data))
            else:
                raise TypeError("expected a datetime or timedelta object")
        else:
            self.reminders.append(reminder(message.nick, message.nick, datetime.datetime.today(),
                                           datetime.datetime.today() + datetime.timedelta(0, 10), "", message.params,
                                           message.server))
            yield message.reply("reminder set!")
        self.reminders.sort()
        self.event.set()


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