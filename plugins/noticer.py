from wrappers import *

@plugin
class noticer:

    @extension(priority=10, type=extensiontype.command)
    @extension(priority=10, type=extensiontype.regex)
    @extension(priority=10, type=extensiontype.trigger)
    @extension(priority=10, type=extensiontype.event)
    def notice(self, message):
        if message.command == "PRIVMSG" and not message.ctcp:
            x = message.copy()
            x.command = "NOTICE"
            return x
        return message