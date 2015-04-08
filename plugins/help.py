from wrappers import *
from inspect import getdoc

@plugin
class Help:

    @command("list")
    def list(self, message):
        """list the loaded plugins"""
        return message.reply(list(self.bot.plugins.keys()), "loaded plugins: " + ", ".join(self.bot.plugins.keys()))

    @command("commands")
    def listcoms(self, message):
        """list the available commands"""
        return message.reply(list(self.bot.commands.keys()), "available commands: " + ", ".join(self.bot.plugins.keys()))

    @command("aliases")
    def listaliases(self, message):
        """list the saved aliases"""
        return message.reply(list(self.bot.aliases.keys()), "saved aliases: " + ", ".join(self.bot.plugins.keys()))

    @command("expand")
    def expand(self, message):
        """show what an alias does"""
        if message.text:
            command = message.text.split()[0].strip()
            if command in self.bot.aliases:
                x = self.bot.aliases[command]
                x = self.bot.command_char+ "alias %s = " % command + " || ".join(["%s%s" % (cmd, (" " + arg) if arg else "") for cmd, arg in x])
                return message.reply(x)

    @command("help", simple=True)
    def help_(self, message):
        """help <command> => returns the help for the specified command"""
        if not isinstance(message.data, str):
            doc = getdoc(message.data)
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