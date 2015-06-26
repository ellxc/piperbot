import urllib.request
import urllib.error
import urllib.parse
import html
import json
import http
from wrappers import *


@plugin
class linker:
    urlpattern = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

    @regex(r"(?:^|\s+)/r/([a-zA-Z0-9]+)(?:$|\s+)")
    def reddit(self, message):
        if not message.text.startswith("Title:"):
            return message.reply("http://reddit.com/r/" + message.groups)

    @command
    def shurl(self, message):
        url = str(message.data)

        if self.urlpattern.match(url):
            gurl = "https://api-ssl.bitly.com/v3/shorten?login=elliotxc&apiKey=R_e3a81272a9644dccb7c84b218d699d9f&format=txt&longUrl=%s" % urllib.parse.quote(url)
            req = urllib.request.Request(gurl)
            results = urllib.request.urlopen(req).read().decode()
            return message.reply(results)
        else:
            raise ValueError("not a valid url")

    @adv_command
    def burl(self, arg, target):
        url = arg.text
        try:
            x = yield
            link = url + urllib.parse.urlencode(x.data)
            target.send(x.reply(link))
        except GeneratorExit:
            target.close()
