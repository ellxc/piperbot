import codecs

from wrappers import *


def lup():
    while 1: pass


@plugin(desc="general")
class general():
    sedcommand = re.compile(r"s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1((?:(?!\1)[^\\]|\\.)*)\1?([gi\d]*) ?(.*)")
    itersplit = re.compile(r'(?:"[^"]*"|[^ ]+)')

    @command  # (groups="^(\S+)?$")
    def pm(self, messsage):
        x = messsage.copy()
        x.params = messsage.nick
        yield x


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
        yield message.reply(message.text)

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
        yield message.reply("loaded plugins : " + ", ".join(self.bot.plugins.keys()))

    @command("tr")
    def tr(self, message):
        yield message.reply()

    @command("help")
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
                yield message.reply(doc.split("\n")[0])

    @command
    def strip(self, message):
        yield message.reply(message.text.strip())

    @command
    def blank(self, message):
        yield message.reply("", data=message.data)


    @regex(r"^s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1((?:(?!\1)[^\\]|\\.)*)\1([gi\d]*)")
    @command("sed")
    def sed(self, message):
        text = None
        if message.groups:
            print(message.groups)
            delim, find, sub, flags = message.groups
        else:
            match = self.sedcommand.search(message.text)
            if match:
                delim, find, sub, flags, text = match.groups()

        if message.groups or match:
            sub = re.sub(r"\\/", "/", sub, count=0)
            action = False
            kwargs = {"count": 1}
            if "i" in flags:
                kwargs["flags"] = re.IGNORECASE
            if not text:
                for msg in list(self.bot.message_buffer[message.server][message.params])[1:]:
                    matchobj = timed(lambda:
                                     bool(re.search(find, msg.text,
                                                    **({"flags": re.IGNORECASE} if "i" in flags else {}))))
                    if matchobj:
                        text = msg.text
                        if msg.action:
                            action = True
                        break
                if not text:
                    raise Exception("No text and no matching message found")
            if not sub:
                sub = ""
            index = re.search(r".*?(\d+)", flags)
            if "g" not in flags and index is not None:
                index = int(index.group(1))
                text = timed(lambda: [text[:x.start()] + x.expand(sub) + text[x.end():] for x in [[x for x, y in zip(re.finditer(find, text, **({"flags": re.IGNORECASE} if "i" in flags else {})), range(index))][-1]]][0]) # erm ... basically get the nth matchobject and do stuff
                result = message.reply(text)
                #result = message.reply(timed(re.sub, args=(find, replaceNthWith(index, sub), text)))    # more readable but also less efficient!
            else:
                if "g" in flags:
                    kwargs["count"] = 0
                result = message.reply(timed(re.sub, args=(find, sub, text), kwargs=kwargs))

            if action:
                result.action = True
            yield result

        else:
            raise Exception("invalid pattern")


def replaceNthWith(n, replacement):
    def replace(match, c=[0]):
        c[0] += 1
        return match.expand(replacement) if c[0] == n else match.group(0)

    return replace
