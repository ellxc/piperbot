from wrappers import *

@plugin(desc="sending tools")
class sender:
    @command("channel")
    def channel(self,message):
        response = message.copy()
        args = message.text.split()
        channels = []
        for arg in args:
            if arg and arg[0] in "#&!+":
                if arg not in self.bot.servers[message.server]:
                    raise Exception("not in channel specified")
                channels.append(arg)
            else:
                break
        if not channels:
            raise Exception("no channel specified")
        for channel in channels:
            response.params = channel
            yield response
            
    @command("send")
    def channel(self,message):
        response = message.copy()
        args = message.text.split()
        server = ""
        channels = []
        if args and args[0] and args[0] in self.bot.servers:
            server = args[0]
            args = args[1:]
        for arg in args:
            if arg and arg[0] in "#&!+":
                if arg not in self.bot.servers[message.server]:
                    raise Exception("not in channel specified")
                channels.append(arg)
            else:
                break
        if not channels:
            raise Exception("no channel specified")
        for channel in channels:
            response.params = channel
            yield response        