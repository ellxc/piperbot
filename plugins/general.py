import codecs
import re
import multiprocessing

from plugins.stuff.BasePlugin import *


@plugin(desc="general")
class general():

    sedcommand = re.compile(r"s/((?:[^\\/]|\\.)*)/((?:[^\\/]|\\.)*)/([gi]*)(?: (.*))?")
    itersplit = re.compile(r'(?:"[^"]*"|[^ ]+)')


    #@command("iterate")
    def iter(self, message):
        for x in self.itersplit.finditer(message.text):
            yield message.reply(x.group(0))

    @command("r")
    @command("reverse")
    def reverse(self, message):
        response = message.get_reply()
        response.text = response.text[::-1]
        yield response

    @command("echo")
    def echo(self, message):
        yield message

    @command("caps")
    @command("upper")
    def uper(self, message):
        response = message.get_reply()
        response.text = response.text.upper()
        yield response

    @command("lower")
    def lower(self, message):
        response = message.get_reply()
        response.text = response.text.lower()
        yield response

    @command("rot13")
    def rot13(self, message):
        response = message.get_reply()
        response.text = codecs.encode(response.text, 'rot_13')
        yield response

    @command("title")
    @command("camel")
    def camel(self, message):
        response = message.get_reply()
        response.text = response.text.title()
        yield response

    @command("b")
    @command("bin")
    @command("binary")
    def binary(self, message):
        response = message.get_reply()
        try:
            number = int(message.text)
            response.text = "{0:b}".format(number)
            yield response
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("-b")
    @command("-bin")
    @command("-binary")
    def reversebinary(self, message):
        response = message.get_reply()
        try:
            number = int(message.text, 2)
            response.text = str(number)
            yield response
        except Exception as e:
            raise Exception("failed to parse: " + str(e))

    @command("h")
    @command("hex")
    def hex(self, message):
        response = message.get_reply()
        try:
            number = int(message.text)
            response.text = "{0:x}".format(number)
            yield response
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

    @regex(r"^s/((?:[^\\/]|\\.)*)/((?:[^\\/]|\\.)*)(?:/([gi]*))?")
    @command("sed")
    def sed(self, message):
        response = message.get_reply()
        text = None
        if message.groups:
            print(message.groups)
            find, sub, flags = message.groups
            if not flags: flags = ""
        else:
            match = self.sedcommand.search(message.text)
            if match:
                find, sub, flags, text = match.groups()
                if not flags: flags = ""
        
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
                        matchobj = re.search(find, msg.text, flags=re.IGNORECASE)
                    else:
                        matchobj = re.search(find, msg.text)
                    if matchobj:
                        text = msg.text
                        if msg.action:
                            action = True
                        break
                if not text:
                    raise Exception("No text and no matching message found")
            if not sub:
                sub = ""
            temp1, temp2 = multiprocessing.Pipe()
            proc = multiprocessing.Process(target=self.dosed, args=(temp2, find, sub, text), kwargs=kwargs)
            proc.start()
            if temp1.poll(2):
                response.text = temp1.recv()
                response.text = response.text.replace("\n", "\\n").replace("\r", "\\r")
                response.action = action

                yield response
            else:
                proc.terminate()
                raise Exception("took too long")
                        
        else:
            raise Exception("invalid pattern")

    def dosed(self, pipe, find, sub, text, **kwargs):
        pipe.send(re.sub(find, sub, text, **kwargs))