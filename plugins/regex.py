import re
from wrappers import *
from Message import Message

@plugin
class regexes:
    sedcommand = re.compile(r"^ *s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1?((?:(?!\1)[^\\]|\\.)*)\1([gi\d]*)(?: +(.+))?")
    grepcommand = re.compile(r" */(.+)/([i]*)|(.+)")

    @regex(r"^s([:/%|\!@,])((?:(?!\1)[^\\]|\\.)*)\1((?:(?!\1)[^\\]|\\.)*)\1?([gi\d]*)(?: +(.+))?")
    def sedr(self, message):
        print(message.groups)
        delim, find, sub, flags, text = message.groups

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
                    if msg.ctcp == "ACTION":
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
            result.ctcp = "ACTION"
        return result


    @command("sed")
    def sedc(self, arg, target):
        """sed s/find/replace/flags [text] -> accepts piped in text, or if no text is found it will search the previous messages for a match"""
        match = self.sedcommand.search(arg.text)
        if not match:
            raise Exception("invalid pattern")

        delim, find, sub, flags, text = match.groups()

        if text:
            text = self.sub(delim, find, sub, flags, text)
        try:
            while 1:
                x = yield
                if x is None:
                    if not text:
                        for msg in list(self.bot.message_buffer[arg.server][arg.params])[1:]:
                            matchobj = timed(lambda:
                                             bool(re.search(find, msg.text,
                                                            **({"flags": re.IGNORECASE} if "i" in flags else {}))))
                            if matchobj:
                                text = msg.text
                                break
                        if not text:
                            raise Exception("No text and no matching message found")
                    text = self.sub(delim, find, sub, flags, text)
                    target.send(arg.reply(text))
                else:
                    text = self.sub(delim, find, sub, flags, x.text)
                    target.send(x.reply(text))
        except GeneratorExit:
            target.close()



    def sub(self, delim, find, sub, flags, text):
        sub = re.sub(r"\\" + delim, delim, sub)
        action = False
        kwargs = {"count": 1}
        if "i" in flags:
            kwargs["flags"] = re.IGNORECASE
        if not sub:
            sub = ""
        index = re.search(r".*?(\d+)", flags)
        if "g" not in flags and index is not None:
            index = int(index.group(1))
            text = timed(lambda: [text[:x.start()] + x.expand(sub) + text[x.end():] for x in [[x for x, y in zip(re.finditer(find, text, **({"flags": re.IGNORECASE} if "i" in flags else {})), range(index))][-1]]][0]) # erm ... basically get the nth matchobject and do stuff
            result = text
            #result = message.reply(timed(re.sub, args=(find, replaceNthWith(index, sub), text)))    # more readable but also less efficient!
        else:
            if "g" in flags:
                kwargs["count"] = 0
            result = timed(re.sub, args=(find, sub, text), kwargs=kwargs)

        return result

    @command("grep")
    def regex(self, arg, target):
        reg, flags, ftext = self.grepcommand.match(arg.text).groups()
        print(reg, flags, ftext)
        if reg:
            if "i" in flags:
                flags = {"flags": re.IGNORECASE}
            else:
                flags = {}
            reg = re.compile(reg, **flags)
        try:
            if reg:
                while 1:
                    x = yield
                    if x is None:
                        found = False
                        for msg in list(self.bot.message_buffer[arg.server][arg.params])[1:][::-1]:
                            if timed(lambda: bool(reg.search(msg.text))):
                                target.send(msg.copy())
                                found = True
                        if not found:
                            raise Exception("no messages found")
                    else:
                        if timed(lambda: bool(reg.search(x.text))):
                            target.send(x)
            while 1:
                x = yield
                if x is None:
                    found = False
                    for msg in list(self.bot.message_buffer[arg.server][arg.params])[1:][::-1]:
                        if ftext in msg.text:
                            target.send(msg.copy())
                            found = True

                    if not found:
                        raise Exception("no messages found")
                else:
                    if ftext in x.text:
                        target.send(x)
        except GeneratorExit:
            target.close()



def replaceNthWith(n, replacement):
    def replace(match, c=[0]):
        c[0] += 1
        return match.expand(replacement) if c[0] == n else match.group(0)

    return replace