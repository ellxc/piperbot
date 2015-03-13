import codecs
import urllib.request
import urllib.parse

from wrappers import *


@plugin(desc="general")
class general():
    sedcommand = re.compile(r"s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1((?:(?!\1)[^\\]|\\.)*)\1?([gi\d]*) ?(.*)")
    itersplit = re.compile(r'(?:"[^"]*"|[^ ]+)')

    @command  # (groups="^(\S+)?$")
    def pm(self, messsage):
        x = messsage.copy()
        x.params = messsage.nick
        return x


    @command("iterate", adminonly=True, simple=True)
    def iter(self, message):
        for x in self.itersplit.finditer(message.text):
            yield message.reply(x.group(0))

    @command("reverse")
    def reverse(self, message):
        return message.reply(message.text[::-1])

    @command("echo")
    def echo(self, message):
        return message.reply(message.text, data=message.data)

    @command("caps")
    @command("upper")
    def uper(self, message):
        return message.reply(message.text.upper())

    @command("lower")
    def lower(self, message):
        return message.reply(message.text.lower())

    @command("rot13")
    def rot13(self, message):
        return message.reply(codecs.encode(message.text, 'rot_13'))

    @command("camel")
    def camel(self, message):
        return message.reply(message.text.title())

    @command("list")
    def list(self, message):
        return message.reply("loaded plugins : " + ", ".join(self.bot.plugins.keys()))

    @command("tr")
    def tr(self, message):
        return message.reply()

    @command("help")
    def help(self, message):
        """help <command>   -> returns the help for the specified command
           derp derp derp

        """
        if message.data is not None and message._text is None:
            return message.reply(
                text="not yet implemented pydoc look up. this is a %s" % message.data.__class__.__name__)
        else:
            try:
                com = message.text.split()[0]
                func = self.bot.commands[com][0]
            except:
                raise Exception("specifed command not found")
            doc = func.__doc__
            if not doc:
                return message.reply("No help found for specified command")
            else:
                return message.reply(doc.split("\n")[0])

    @command
    def strip(self, message):
        return message.reply(message.text.strip())

    @command
    def blank(self, message):
        return message.reply("", data=message.data)

    @command
    def sprunge(self, arg, target):
        lines = []
        arg = arg
        try:
            while 1:
                x = yield
                if x is None:
                    lines.append(str(arg.text))
                else:
                    lines.append(str(x.text))
        except GeneratorExit:
            data = {'sprunge': '\n'.join(lines)}
            response = urllib.request.urlopen(urllib.request.Request('http://sprunge.us',
                                                                     urllib.parse.urlencode(data).encode(
                                                                         'utf-8'))).read().decode()
            print(response)
            target.send(arg.reply(text=response))
            target.close()

    @command
    def collect(self, arg, target):
        lines = []
        arg = arg
        try:
            while 1:
                x = yield
                if x is None:
                    lines.append(str(arg.text))
                else:
                    lines.append(str(x.text))
        except GeneratorExit:
            target.send(arg.reply(text='; '.join(lines)))
            target.close()

    @regex(r"^s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1((?:(?!\1)[^\\]|\\.)*)\1([gi\d]*)(?: +(.+))")
    def sedr(self, message):
        print(message.groups)
        delim, find, sub, flags, text = message.groups

        sub = re.sub(r"\\" + delim, delim, sub)
        action = False
        kwargs = {"count": 1}
        if "i" in flags:
            kwargs["flags"] = re.IGNORECASE
        if text is None:
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
        else:
            text = self.bot.buffer_replace(text, message.server, message.params, offset=1)

        if not sub:
            sub = ""
        index = re.search(r".*?(\d+)", flags)
        if "g" not in flags and index is not None:
            index = int(index.group(1))
            text = timed(lambda: [text[:x.start()] + x.expand(sub) + text[x.end():] for x in [[x for x, y in zip(
                re.finditer(find, text, **({"flags": re.IGNORECASE} if "i" in flags else {})), range(index))][-1]]][
                0])  # erm ... basically get the nth matchobject and do stuff
            result = message.reply(text)
            # result = message.reply(timed(re.sub, args=(find, replaceNthWith(index, sub), text)))    # more readable but also less efficient!
        else:
            if "g" in flags:
                kwargs["count"] = 0
            result = message.reply(timed(re.sub, args=(find, sub, text), kwargs=kwargs))

        if action:
            result.action = True
        return result


    @command("sed")
    def sedc(self, message):
        text = None

        match = self.sedcommand.search(message.text)
        if match:
            delim, find, sub, flags, text = match.groups()
            sub = re.sub(r"\\" + delim, delim, sub)
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
            return result

        else:
            raise Exception("invalid pattern")


def replaceNthWith(n, replacement):
    def replace(match, c=[0]):
        c[0] += 1
        return match.expand(replacement) if c[0] == n else match.group(0)

    return replace
