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

    #@regex(r"^.*(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)")
    def url(self, message):
        try:
            local_filename, headers = urllib.request.urlretrieve(message.groups)
            print(headers)
            contenttype = headers.get_content_type()
            encoding = headers.get_content_charset(failobj="")
            if "html" in contenttype:
                url = open(local_filename).read()

                def everything_between(text,begin,end):
                    idx1=text.find(begin)
                    idx2=text.find(end,idx1)
                    return text[idx1+len(begin):idx2].strip()

                title= html.unescape(everything_between(url,'<title>','</title>')[:200])

                return message.reply("Title: %s" % title)
            else:
                return message.reply("[%s%s]" % (contenttype, ("; encoding=" + encoding) if encoding else ""))

        except urllib.error.HTTPError as e:
            pass
        except Exception as e:
            print(e)
            return message.reply("Title: pron")
        finally:
            urllib.request.urlcleanup()

    @command
    def shurl(self, message):
        url = str(message.data)

        if self.urlpattern.match(url):
            gurl = "https://api-ssl.bitly.com/v3/shorten?login=elliotxc&apiKey=R_e3a81272a9644dccb7c84b218d699d9f&format=txt&longUrl=%s" % urllib.parse.quote(url)
            req = urllib.request.Request(gurl)
            results = urllib.request.urlopen(req).read().decode()
            print(results)
            return message.reply(results)
        else:
            raise ValueError("not a valid url")

    @command
    def burl(self, arg, target):
        url = arg.text
        try:
            x = yield
            link = url + urllib.parse.urlencode(x.data)
            target.send(x.reply(link))
        except GeneratorExit:
            target.close()
