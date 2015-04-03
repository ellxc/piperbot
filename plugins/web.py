from wrappers import *
import requests
import lxml.etree
import urllib.parse
import math
from collections import defaultdict
from itertools import zip_longest
import re
from os.path import splitext
from dateutil import parser
import os
from io import BytesIO
from PyPDF2 import PdfFileReader


class Specials:
    DEFAULT_HEADERS = {
        "Accept-Encoding": "utf-8",
        "User-Agent": 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13'
                      '(KHTML, like Gecko) Version/3.1 Safari/525.13'
    }

    @staticmethod
    def youtube(url):
        youtuberegex = re.compile(r"(?:.*v=|https://youtu\.be/)([^&]+?)(?:[/&].*)?$")
        # http://gdata.youtube.com/feeds/api/videos/
        vid = youtuberegex.match(url).group(1)

        url = "http://gdata.youtube.com/feeds/api/videos/" + vid
        myparser = lxml.etree.HTMLParser(encoding="utf-8")
        tree = lxml.etree.parse(url, myparser)

        title = tree.xpath('//*[name()="title"][1]/text()')[0]
        seconds = int(tree.xpath('//*[local-name() = "duration"]/@seconds')[0])
        publishedon = str(parser.parse(tree.xpath('//*[name()="published"]/text()')[0]).date())
        publishedby = tree.xpath('//*[name()="author"]/*[name()="name"]/text()')[0]
        views = format(int(tree.xpath('//*[local-name() = "statistics"]/@viewCount')[0]), ",d")
        print(seconds)

        if seconds == 0:
            duration = " [LIVE]"
            views += " viewers"
        else:
            hours = seconds // 3600
            minutes = (seconds - (hours*3600)) // 60
            seconds = seconds - (hours*3600) - (minutes*60)
            duration = " [{}{:02d}:{:02d}]".format((str(hours) + ":") if hours else "", minutes, seconds)
            views += " views"

        yield "YouTube: %s%s %s Posted on %s by %s" % (title, duration, views, publishedon, publishedby)

    @staticmethod
    def wikipediaparse(url):
        page = requests.get(url, headers=Specials.DEFAULT_HEADERS)
        myparser = lxml.etree.HTMLParser(encoding="utf-8")
        tree = lxml.etree.HTML(page.text, parser=myparser)
        yield "".join(tree.xpath("//title/text()")).split()[0] + ": " +\
              "".join(tree.xpath('//*[@id="mw-content-text"]/p[1]/*[not(name()="sup")]//text()'
                                 '| //*[@id="mw-content-text"]/p[1]/text()'))

    @staticmethod
    def urbandictionaryparse(url):
        page = requests.get(url, headers=Specials.DEFAULT_HEADERS)
        myparser = lxml.etree.HTMLParser(encoding="utf-8")
        tree = lxml.etree.HTML(page.text, parser=myparser)
        for defpanel in tree.xpath('//div[@class="def-panel"]'):
            meaning = " ".join(map(lambda x: x.strip(), defpanel.xpath('./div[@class="meaning"]//text()')))
            example = " ".join(map(lambda x: x.strip(), defpanel.xpath('./div[@class="example"]//text()')))
            yield "Urban Dictionary: " + "".join(meaning) + ((' "%s"' % example)
                                                             if example and len(example) + len(meaning) < 300 else "")

    @staticmethod
    def read_pdf_metadata(url):
        metadata_regex = re.compile('(?:/(\w+)\s?\(([^\n\r]*)\)\n?\r?)', re.S)

        request = requests.get(url, stream=True)

        stream = BytesIO(request.content)

        contentstats = URL.get_content_stats(request.headers)

        stream.seek(-2048, os.SEEK_END)
        try:
            properties = dict(('/' + p.group(1), p.group(2))
                              for p in metadata_regex.finditer(str(stream.read(2048))))
            if '/Title' in properties:
                return ["PDF: %s" % properties['/Title']]
        except UnicodeDecodeError:
            properties.clear()

        properties = PdfFileReader(stream).documentInfo
        if '/Title' in properties:
            return ["PDF: %s%s" % (properties['/Title'], (" [%s]" % contentstats) if contentstats else "")]
        return []

    @staticmethod
    def imgur(url):
        head = requests.head(url, timeout=5)
        print(head.headers)
        contentstats = ""
        if not (url.endswith(".gifv") or url.endswith(".gif")):
            contentstats = URL.get_content_stats(head.headers)

        titlepage = splitext(url)[0]
        page = requests.get(titlepage, headers=Specials.DEFAULT_HEADERS, stream=True)

        myparser = lxml.etree.HTMLParser(encoding="utf-8")
        tree = lxml.etree.HTML(page, parser=myparser)

        title = "".join(tree.xpath('//*[@id="image-title"]/text()')).strip()

        yield (("imgur: "+title+" ") if title else "") + (("[%s]" % contentstats) if contentstats else "")


@plugin
class URL:
    TIMEOUT = 5
    UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    DEFAULT_HEADERS = {
        "Accept-Encoding": "utf-8",
        # Safari user agent
        "User-Agent": 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13'
                      '(KHTML, like Gecko) Version/3.1 Safari/525.13'
    }

    SPECIAL_HANDLERS = {
        r".*\.wikipedia\.org": Specials.wikipediaparse,
        r"www\.urbandictionary\.com\/define": Specials.urbandictionaryparse,
        r"imgur\.com/.+\..+": Specials.imgur,
        r"youtube\.com/watch\?.+v=": Specials.youtube,
        r"youtu\.be/.+": Specials.youtube,
        r"\.pdf": Specials.read_pdf_metadata,
    }

    @regex(r"((?:http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)")
    def url(self, message):
        if message.text[0] not in "!#.$%":
            link = message.groups

            if not link.startswith("http"):
                link = "http://" + link

            for pattern, handler in URL.SPECIAL_HANDLERS.items():
                if re.search(pattern, link):
                        for response in handler(link):
                            return message.reply(response)

            # Get the HTTP headers and look for some content statistics...
            head_repsonse = requests.head(link, timeout=URL.TIMEOUT)
            headers = head_repsonse.headers
            content_stats = self.get_content_stats(headers)

            if "html" in headers['content-type']:
                myparser = lxml.etree.HTMLParser(encoding="utf-8")
                page = requests.get(link, headers=URL.DEFAULT_HEADERS, stream=True)
                for chunk in page.iter_content(chunk_size=4096):
                    fragment = lxml.etree.HTML(chunk, parser=myparser)
                    title = fragment.xpath("//title/text()")
                    if title:
                        title = "Title: " + title[0].strip().replace("\n", "")

                        # If this is a redirect response, and we're actually being redirected somewhere
                        if head_repsonse.status_code in [301, 302, 303, 304, 307] and \
                           page.url not in link and link not in page.url:
                            title += " - Redirects to: %s" % page.url

                        return message.reply(title)

            if content_stats:
                return message.reply("[%s]" % content_stats)

    @staticmethod
    def get_content_stats(headers):
        content_stats = ""
        if "content-type" in headers:
            content_stats += headers['content-type']
        if "content-length" in headers:
            print(int(headers["content-length"]))
            content_stats += " " + URL.human_data_size(int(headers["content-length"]))
        return content_stats

    @staticmethod
    def human_data_size(byte_count):
        if byte_count == 0:
            return "0" + URL.UNITS[0]
        place = (math.floor(math.log(byte_count, 1024)))
        num = byte_count / math.pow(1024, place)
        return "{:.2f} {}".format(num, URL.UNITS[place])


@plugin
class Searcher:
    @command("g", simple=True)
    def search(self, message):
        query = "http://www.google.co.uk/search?q=" + urllib.parse.quote(message.data)

        page = requests.get(query, headers=URL.DEFAULT_HEADERS)
        myparser = lxml.etree.HTMLParser(encoding="utf-8")
        tree = lxml.etree.HTML(page, parser=myparser)

        result = tree.xpath('(//*[@class="r"])[1]//text()')
        resultlink = tree.xpath('(//*[@class="r"])[1]//@href')
        if resultlink:
            resultlink = urllib.parse.parse_qs(urllib.parse.urlparse("test.com" + resultlink[0]).query)["q"][0] if \
                resultlink[0].startswith("/url?") else resultlink[0]

        weather = tree.xpath('//div[@class="e"][1]')
        if weather:
            *title, weather, source = weather[0].xpath('./h3//text() | ./table')
            weather = "".join(weather.xpath(
                './tr[1]/td[2]/span/text() | ./tr[3]/td/text() | ./tr[4]/td//text() | ./tr[5]/td[1]/text()'))
            weather = "".join(title) + " " + weather

        definitionsets = list(grouper(
            tree.xpath('//li[@class="g"][1]/div[not(@class="e")]/h3 | //li[@class="g"][1]/div[not(@class="e")]/table'),
            2))

        definitions = defaultdict(list)

        for h3, table in definitionsets:
            definitiontypes = list(grouper(table.xpath("./tr/td/div/text() | ./tr/td/ol"), 2))
            for d_type, ol in definitiontypes:
                dfns = ol.xpath("./li/text()")
                definitions[d_type].extend(dfns)

        if definitions:
            for dfntype, dfns in definitions.items():
                yield message.reply(dfntype + ": " + " ".join(dfns[:1]))
        elif weather:
            yield message.reply(weather)
        else:
            responded = False
            for pattern, handler in URL.SPECIAL_HANDLERS.items():
                if resultlink and re.search(pattern, resultlink):
                    for response in handler(resultlink):
                        yield message.reply("top result: %s" % resultlink)
                        yield message.reply(response)
                        responded = True
                        break
            if not responded:
                if resultlink:
                    yield message.reply("top result: %s %s" % ("".join(result), resultlink))
                elif result:
                    yield message.reply("result: %s" % "".join(result))


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
