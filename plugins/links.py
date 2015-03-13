import urllib.request
import urllib.error
import html

from wrappers import *


@plugin
class linker:


    @regex(r"(?:^|\s+)/r/([a-zA-Z0-9]+)(?:$|\s+)")
    def reddit(self, message):
        if not message.text.startswith("Title:"):
            return message.reply("http://reddit.com/r/" + message.groups)

    @regex(r"^.*(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)")
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
