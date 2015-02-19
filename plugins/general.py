import codecs
import re
import time

from wrappers import *

def lup():
    while 1: pass

@plugin(desc="general")
class general():

    sedcommand = re.compile(r"s/((?:[^\\/]|\\.)*)/((?:[^\\/]|\\.)*)/([gi]*)(?: (.*))?")
    itersplit = re.compile(r'(?:"[^"]*"|[^ ]+)')


    @command("iterate", adminonly=True)
    def iter(self, message):
        for x in self.itersplit.finditer(message.text):
            yield message.reply(x.group(0))

    @command("r")
    @command("reverse")
    def reverse(self, message):
        yield message.reply(message.text[::-1])

    @command("echo")
    def echo(self, message):
        yield message

    @command("caps")
    @command("upper")
    def uper(self, message):
        yield message.reply(message.text.upper())

    @command("lower")
    def lower(self, message):
        yield message.reply(message.text.lower())

    @command("rot13")
    def rot13(self, message):
        yield message.reply(codecs.encode(message.text, 'rot_13'))

    @command("title")
    @command("camel")
    def camel(self, message):
        yield message.reply(message.text.title())

    @command("b")
    @command("bin")
    @command("binary")
    def binary(self, message):
        try:
            number = int(message.text)
            yield message.reply("{0:b}".format(number))
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("-b")
    @command("-bin")
    @command("-binary")
    def reversebinary(self, message):
        try:
            number = int(message.text, 2)
            yield message.reply(str(number))
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("h")
    @command("hex")
    def hex(self, message):
        response = message.get_reply()
        try:
            number = int(message.text)
            yield message.reply("{0:x}".format(number))
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("-h")
    @command("-hex")
    def reversehex(self, message):
        try:
            number = int(message.text, 16)
            text = str(number)
            yield message.reply(text)
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("list")
    def list(self, message):
        yield message.reply( "loaded plugins : " + ", ".join(self.bot.plugins.keys()) )

    @command("tr")
    def tr(self, message):
        yield message.reply()

    @command("sleep")
    def slp(self, message):
        timed(lup)
        yield message.reply("this message shouldn't get through")



    @regex(r"^s/((?:[^\\/]|\\.)*)/((?:[^\\/]|\\.)*)/([gi]*)")
    @command("sed")
    def sed(self, message):
        text = None
        if message.groups:
            print(message.groups)
            find, sub, flags = message.groups
        else:
            match = self.sedcommand.search(message.text)
            if match:
                find, sub, flags, text = match.groups()
            
        if message.groups or match:
            sub = re.sub(r"\\/", "/", sub, count=0)
            action = False
            kwargs = {}
            if "i" in flags:
                kwargs["flags"] = re.IGNORECASE
            if "g" in flags:
                kwargs["count"] = 0
            else:
                kwargs["count"] = 1
            if not text:
                for msg in list(self.bot.message_buffer[message.server][message.params])[1:]:
                    if "i" in flags:
                        matchobj = timed(hacky, args=(find, msg.text), kwargs={"flags": re.IGNORECASE})
                    else:
                        matchobj = timed(hacky, args=(find, msg.text))
                    if matchobj:
                        text = msg.text
                        if msg.action:
                            action = True
                        break
                if not text:
                    raise Exception("No text and no matching message found")
            if not sub:
                sub = ""
            result = message.reply(timed(re.sub, args=(find, sub, text), kwargs=kwargs))
            if action:
                result.action = True
            yield result
                        
        else:
            raise Exception("invalid pattern")

def hacky(*x,**y):
    return bool(re.search(*x,**y))