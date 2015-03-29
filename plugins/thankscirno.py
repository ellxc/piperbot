from wrappers import *
from datetime import timedelta

@plugin
class thx:

    @trigger(lambda x, bot: x.nick == "CirnoX")
    def thanks(self, message):
        prevmsg = list(self.bot.message_buffer[message.server][message.params])[1]

        for prev in list(self.bot.message_buffer[message.server][message.params])[1:6]:
            if message.timestamp - prev.timestamp > timedelta(seconds=10):
                continue
            if message.text.startswith(prev.nick) and prev.nick not in ["Marvin64", "Gwyn", "Kuddle_Kitty"]:
                return
            if message.text.startswith("!"):
                return

        if prevmsg.nick in ["Marvin64", "Gwyn", "Kuddle_Kitty"]:
            return message.reply("fuck you cirno!")

        if prevmsg.text.startswith(".") and "CirnoX" in prevmsg.text:
            return message.reply("fuck you cirno!")