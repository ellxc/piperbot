from wrappers import *
import requests
import lxml.html, lxml.etree
import html
import urllib.parse
from collections import defaultdict
from itertools import zip_longest
import re
from os.path import splitext
from dateutil import parser
import os
from io import BytesIO
from PyPDF2 import PdfFileReader

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)




units = [
    (1024 ** 5, 'P'),
    (1024 ** 4, 'T'),
    (1024 ** 3, 'G'),
    (1024 ** 2, 'M'),
    (1024 ** 1, 'K'),
    (1024 ** 0, 'B'),
    ]





metadata_regex = re.compile('(?:\/(\w+)\s?\(([^\n\r]*)\)\n?\r?)', re.S)

def read_pdf_metadata(url):
    request = requests.get(url, stream=True)

    stream = BytesIO(request.content)

    contentstats = ""
    if "content-length" in request.headers:
        length = int(request.headers["content-length"])
        if length > 2000000:
            return []
        try:
            length = size(length)
        except:
            length = "0B"
        contentstats = length

    stream.seek(-2048, os.SEEK_END)
    try:
        properties = dict(('/' + p.group(1), p.group(2)) \
            for p in metadata_regex.finditer(str(stream.read(2048))))
        if '/Title' in properties:
            return ["PDF: %s" % properties['/Title']]
    except UnicodeDecodeError:
        properties.clear()

    properties = PdfFileReader(stream).documentInfo
    if '/Title' in properties:
        return ["PDF: %s%s" % (properties['/Title'], (" [%s]" % contentstats) if contentstats else "")]
    return []



def size(bytes):
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = bytes/factor
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return format(amount,".2f") + suffix

youtuberegex = re.compile(r".*v=([^&]+?)(?:&.*)?$")

def youtube(url):
    # http://gdata.youtube.com/feeds/api/videos/
    vid = youtuberegex.match(url).group(1)

    url = "http://gdata.youtube.com/feeds/api/videos/" + vid
    tree = lxml.etree.parse(url)

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
        duration = " [%s%s%s]" % ((str(hours) + ":") if hours else "", (str(minutes)+":") if minutes else "00:", seconds if len(str(seconds)) ==2 else ("0"+str(seconds)))
        views += " views"

    yield "YouTube: %s%s %s Posted on %s by %s" % (title, duration, views, publishedon, publishedby)


def imgur(url):
    head = requests.head(url, timeout=5)
    print(head.headers)
    contentstats = ""
    if not (url.endswith(".gifv") or url.endswith(".gif")):
        if "content-type" in head.headers:
            contentstats += head.headers["content-type"]
        if "content-length" in head.headers:
            length = int(head.headers["content-length"])
            if length > 0:
                length = size(length)
            else:
                length = "0B"
            if contentstats:
                contentstats += "; "
            contentstats += length

    titlepage = splitext(url)[0]
    page = requests.get(titlepage, headers=headers, stream=True)

    tree = lxml.html.fromstring(page.content)

    title = "".join(tree.xpath('//*[@id="image-title"]/text()')).strip()

    yield (("imgur: "+title+" ") if title else "") + (("[%s]" % contentstats) if contentstats else "")



def wikipediaparse(url):
    page = requests.get(url, headers=headers)
    tree = lxml.html.fromstring(page.text)
    yield "".join(tree.xpath("//title/text()")).split()[0]+ ": " +\
          "".join(tree.xpath('//*[@id="mw-content-text"]/p[1]/*[not(name()="sup")]//text()'
                             '| //*[@id="mw-content-text"]/p[1]/text()'))


def urbandictionaryparse(url):
    page = requests.get(url, headers=headers)
    tree = lxml.html.fromstring(page.text)
    for defpanel in tree.xpath('//div[@class="def-panel"]'):
        meaning = " ".join(map(lambda x: x.strip(), defpanel.xpath('./div[@class="meaning"]//text()')))
        example = " ".join(map(lambda x: x.strip(), defpanel.xpath('./div[@class="example"]//text()')))
        yield "Urban Dictionary: " + "".join(meaning) + ((' "%s"' % example) if example and len(example) + len(meaning) < 300 else "")

headers = {'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13'}

websitehandlers = {
            r".*\.wikipedia\.org": wikipediaparse,
            r"www\.urbandictionary\.com\/define": urbandictionaryparse,
            r"imgur\.com/.+\..+": imgur,
            r"youtube\.com/watch\?v=": youtube,
            r"\.pdf": read_pdf_metadata,
        }


@plugin
class url:

    @regex(r"^.*((?:http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)")
    def url(self, message):
        link = message.groups

        if not link.startswith("http"):
            link = "http://"+link


        for pattern, handler in websitehandlers.items():
            if re.search(pattern, link):
                for response in handler(link):
                    return message.reply(response)

        headers = requests.head(link, timeout=5)
        print(headers.status_code)
        contentstats = ""
        if "content-type" in headers.headers:
            contentstats += headers.headers["content-type"]
        if "content-length" in headers.headers:
            try:
                length = size(int(headers.headers["content-length"]))
            except:
                length = "0B"
            contentstats += "; " + length
        if "html" in contentstats.lower():
            page = requests.get(link, stream=True)
            for chunk in page.iter_content(chunk_size=4096):
                brokenhtml = lxml.html.fromstring(chunk)
                title = brokenhtml.xpath("//title/text()")
                if title:
                    title = "Title: " + title[0].strip().replace("\n", "")
                    if headers.status_code in [301, 302, 303, 304, 307]:
                        title += " - Redirects to: %s" % page.url
                    return message.reply(title)
        if contentstats:
            return message.reply("[%s]" % contentstats)








@plugin
class searcher:


    @command("g", simple=True)
    def search(self, message):
        query = "http://www.google.co.uk/search?q=" + urllib.parse.quote(message.data)

        page = requests.get(query, headers=headers)
        tree = lxml.html.fromstring(page.text)


        result = tree.xpath('(//*[@class="r"])[1]//text()')
        resultlink = tree.xpath('(//*[@class="r"])[1]//@href')
        if resultlink:
            resultlink = urllib.parse.parse_qs(urllib.parse.urlparse("test.com"+resultlink[0]).query)["q"][0] if resultlink[0].startswith("/url?") else resultlink[0]

        weather = tree.xpath('//div[@class="e"][1]')
        if weather:
            *title, weather, source = weather[0].xpath('./h3//text() | ./table')
            weather = "".join(weather.xpath('./tr[1]/td[2]/span/text() | ./tr[3]/td/text() | ./tr[4]/td//text() | ./tr[5]/td[1]/text()'))
            weather = "".join(title) + " " + weather



        definitionsets = list(grouper(tree.xpath('//li[@class="g"][1]/div[not(@class="e")]/h3 | //li[@class="g"][1]/div[not(@class="e")]/table'), 2))

        definitions = defaultdict(list)

        for h3, table in definitionsets:
            definitiontypes = list(grouper(table.xpath("./tr/td/div/text() | ./tr/td/ol"), 2))
            for type, ol in definitiontypes:
                dfns = ol.xpath("./li/text()")
                definitions[type].extend(dfns)


        if definitions:
            for dfntype, dfns in definitions.items():
                yield message.reply(dfntype + ": " + " ".join(dfns[:1]))
        elif weather:
            yield message.reply(weather)
        else:
            responded = False
            for pattern, handler in websitehandlers.items():
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



