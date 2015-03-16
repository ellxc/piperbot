import codecs
import urllib.request
import urllib.parse

from wrappers import *


@plugin(desc="general")
class general():
    itersplit = re.compile(r'(?:"[^"]*"|[^ ]+)')

    @command  # (groups="^(\S+)?$")
    def pm(self, arg, target):
        """redirects the output to a private message"""
        try:
            while 1:
                x = yield
                if x is not None:
                    x = x.copy()
                    x.params = arg.nick
                    target.send(x)
        except GeneratorExit:
            target.close()


    @command("iterate", simple=True)
    def iter(self, message):
        for x in self.itersplit.finditer(message.text):
            yield message.reply(x.group(0))

    @command("reverse")
    def reverse(self, message):
        "reverse the message's text"
        return message.reply(message.text[::-1])

    @command("echo")
    def echo(self, message):
        "repeats the input, useful for formatting"
        return message.reply(message.text, data=message.data)

    @command("caps")
    @command("upper")
    def uper(self, message):
        "turns the message into upper case"
        return message.reply(message.text.upper())

    @command("lower")
    def lower(self, message):
        "turns the message into lower case"
        return message.reply(message.text.lower())

    @command("rot13")
    def rot13(self, message):
        "applies rot13 to the message"
        return message.reply(codecs.encode(message.text, 'rot_13'))

    @command("camel")
    def camel(self, message):
        "turns the message into camel case"
        return message.reply(message.text.title())

    @command("list")
    def list(self, message):
        "list the loaded plugins"
        return message.reply("loaded plugins : " + ", ".join(self.bot.plugins.keys()))

    @command("help", simple=True)
    def help(self, message):
        """help <command>   -> returns the help for the specified command
           derp derp derp

        """
        if message.data is not None and message._text is None:
            yield message.reply(
                text="not yet implemented pydoc look up. this is a %s" % message.data.__class__.__name__)
        else:
            try:
                com = message.text.split()[0]
                func = self.bot.commands[com][0]
            except:
                raise Exception("specifed command not found")
            doc = func.__doc__
            if not doc:
                yield message.reply("No help found for specified command")
            else:
                doc = "%s: %s" % (com, doc.split("\n")[0])
                for doc in doc.split(". "):
                    yield message.reply(doc)

    @command
    def strip(self, message):
        "strip the message of any whitespace"
        return message.reply(message.text.strip())

    @command
    def quote(self, message):
        """capture the N number of previous messages and and output it as data"""
        try:
            count = int(message.text or 1)
        except:
            raise Exception("needs an integer for number of lines")

        lines = list(self.bot.message_buffer[message.server][message.params])[1:count + 1][::-1]
        count = len(lines)
        lines = "\n".join([x.to_pretty() for x in lines])

        return message.reply("captured %s lines!" % count, data=lines)

    @command
    def sprunge(self, arg, target):
        """redirect output to a sprunge and return the link"""
        lines = []
        arg = arg
        try:
            while 1:
                x = yield
                if x is None:
                    lines.append(str(arg.text))
                else:
                    lines.append(str(x.data))
        except GeneratorExit:
            if lines:
                data = {'sprunge': '\n'.join(lines)}
                response = urllib.request.urlopen(urllib.request.Request('http://sprunge.us',
                                                                         urllib.parse.urlencode(data).encode(
                                                                             'utf-8'))).read().decode()
                target.send(arg.reply(text=response))
            target.close()

    @command
    def cat(self, arg, target):
        """concat all messages to one line joined by arg.text or ' '"""
        lines = []
        joiner = arg.text or " "
        try:
            while 1:
                x = yield
                if x is None:
                    pass
                else:
                    lines.append(str(x.text))
        except GeneratorExit:
            target.send(arg.reply(text=joiner.join(lines)))
            target.close()

    @command
    def wc(self, arg, target):
        count = 0
        try:
            while 1:
                x = yield
                if x is None:
                    pass
                else:
                    count+=1
        except GeneratorExit:
            target.send(arg.reply(data=count))
            target.close()


