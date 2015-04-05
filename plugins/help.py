from wrappers import *
from inspect import getdoc

@plugin
class Help:

    @command("help", simple=True)
    def help_(self, message):
        """help <command> => returns the help for the specified command"""
        if not isinstance(message.data, str):
            doc = inspect.getdoc(message.data)
            if not doc:
                return message.reply("No help found for passed object '%s'" % message.data.__class__.__name__)
            else:
                firstline = "%s: %s" % (message.data.__class__.__name__, doc.split("\n")[0])
                return message.reply(doc, firstline)
        elif message.data:
            try:
                com = message.data.split()[0]
                func = self.bot.commands[com][0]
            except:
                raise Exception("specifed command not found")
            doc = func.__doc__
            if not doc:
                return message.reply("No help found for specified command")
            else:
                firstline = "%s: %s" % (com, doc.split("\n")[0])
                return message.reply(doc, firstline)
        else:
            return message.reply("Help can be found at https://github.com/ellxc/piperbot/blob/master/README.md or by joining #piperbot on freenode")