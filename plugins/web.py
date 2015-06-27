from wrappers import *
import requests
import re
import os
import json
from io import BytesIO
from PyPDF2 import PdfFileReader
from os.path import splitext
from dateutil import parser
from html.parser import HTMLParser
from bs4 import BeautifulSoup

try:
    import lxml

    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

units = [
    (1024 ** 5, 'P'),
    (1024 ** 4, 'T'),
    (1024 ** 3, 'G'),
    (1024 ** 2, 'M'),
    (1024 ** 1, 'K'),
    (1024 ** 0, 'B'),
]

metadata_regex = re.compile('(?:/(\w+)\s?\(([^\n\r]*)\)\n?\r?)', re.S)


def read_pdf_metadata(url):
    request = requests.get(url, stream=True)

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

    stream = BytesIO(request.content)
    stream.seek(-2048, os.SEEK_END)
    properties = PdfFileReader(stream).documentInfo
    data = {}
    for key, value in properties.items():
        if key.startswith("/"):
            data[key[1:].lower()] = value
        else:
            data[key.lower()] = value

    if 'title' in data:
        return data, "PDF: %s%s" % (data['title'], ((" [%s]" % contentstats) if contentstats else ""))
    return data, (" [%s]" % contentstats) if contentstats else ""


def size(bytes):
    for factor, suffix in units:
        if bytes >= factor:
            break
    amount = bytes / factor
    if isinstance(suffix, tuple):
        singular, multiple = suffix
        if amount == 1:
            suffix = singular
        else:
            suffix = multiple
    return format(amount, ".2f") + suffix


youtuberegex = re.compile(r"(?:.*v=|https://youtu\.be\/)([^&]+?)(?:[\/&?].*)?$")


def youtube(url):
    # http://gdata.youtube.com/feeds/api/videos/
    vid = youtuberegex.match(url).group(1)

    url = "http://gdata.youtube.com/feeds/api/videos/" + vid + "?alt=json"
    page = requests.get(url, headers=headers, stream=True)
    data = json.loads(page.content.decode())
    duration = int(data["entry"]["media$group"]["yt$duration"]["seconds"])
    uploader = data["entry"]["author"][0]["name"]["$t"]
    title = data["entry"]["title"]["$t"]
    viewcount = int(data["entry"]["yt$statistics"]["viewCount"])
    uploaded = parser.parse(data["entry"]["published"]["$t"])

    data = {
        "duration": duration,
        "uploader": uploader,
        "title": title,
        "viewcount": viewcount,
        "uploaded": uploaded,
    }

    h, s = divmod(duration, 60)
    h, m = divmod(h, 60)
    time = " [%d:%02d:%02d]" % (h, m, s)

    message = "YouTube: %s%s %s views, Posted on %s by %s" % (
        title, time, "{:,}".format(viewcount), uploaded.date(), uploader)

    return data, message


def amazon(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, PARSER)

    data = {
        "title":"404",
        "solby":"",
        "price":"",
        "rating": "",
        "noreviews": "",
    }

    title = soup.select("#productTitle")
    if title:
        data["title"] = title[0].get_text()

    soldby = soup.select("#merchant-info > a")
    if soldby:
        data["solby"] = soldby[0].get_text()

    price = soup.select("#priceblock_ourprice")
    if price:
        data["price"] = price[0].get_text()
    else:
        price = soup.select(".a-color-price")
        if price:
            data["price"] = price[0].get_text()

    rating = soup.select("#avgRating > span")
    if rating:
        data["rating"] = rating[0].get_text()
    noreviews = soup.select("#acrCustomerReviewText")
    if noreviews:
        data["noreviews"] = noreviews[0].get_text()

    message = "amazon: " + data["title"]+ " " + data["price"] + ((" sold by " + data["solby"]) if data["solby"] else "") +\
              ((data["rating"] + data["noreviews"]) if data["rating"] else "")

    return data, message

def imgur(url):
    head = requests.head(url, timeout=5)
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

    soup = BeautifulSoup(page.content, PARSER)
    title = soup.find_all(id="image-title")
    if title:
        title = title[0].get_text().strip()

    return {"title": title}, (("imgur: " + title + " ") if title else "") + (
    ("[%s]" % contentstats) if contentstats else "")  #


def wikipediaparse(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, PARSER)
    try:
        title = soup.select(".firstHeading")[0].get_text()
    except:
        title = soup.title.get_text()
    content = "".join(map(lambda x: x.get_text(), soup.select("#mw-content-text > p")[:1]))

    return {"title": title, "content": content}, "Wikipedia: " + content.partition(". ")[0] + "."


def urbandictionaryparse(url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, PARSER)
    for defpanel in soup.select(".def-panel"):
        meaning = " ".join(map(lambda x: x.get_text(), defpanel.select(".meaning")))
        example = " ".join(map(lambda x: x.get_text(), defpanel.select(".example")))
        return {"meaning": meaning, "example": example}, "Urban Dictionary: " + "".join(meaning) + (
        (' "%s"' % example) if example and len(example) + len(meaning) < 300 else "")


headers = {
    'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13'}

websitehandlers = {
    r".*\.wikipedia\.org": wikipediaparse,
    r"www\.urbandictionary\.com\/define": urbandictionaryparse,
    r"imgur\.com/.+\..+": imgur,
    r"youtube\.com/watch": youtube,
    r"youtu\.be/.+": youtube,
    r"\.pdf": read_pdf_metadata,
    r"amazon\..+?\/.+?\/dp": amazon,
}


class TitleHTMLParser(HTMLParser):
    title = ""
    intitle = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.intitle = True
            if self.title:
                self.title += "; "

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.intitle = False

    def handle_data(self, data):
        if self.intitle:
            self.title += data


linkregex = re.compile(r"(?:http[s]?://|www)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")

@plugin
class url:
    def __init__(self):
        self.links = []


    @on_load
    def load(self):
        try:
            with open('links.json', 'r') as infile:
                history = json.load(infile)
                for link in history:
                    self.links.append(link)
        except FileNotFoundError:
            pass


    @on_unload
    def unload(self):
        with open('links.json', 'w') as outfile:
            json.dump(self.links, outfile, sort_keys=True, indent=4, ensure_ascii=False)

    @command("yt")
    @command("youtube")
    def yt(self, message):
        if isinstance(message.data, str):
            urls = message.data.split()
            for x in urls:
                yield message.reply(*youtube(x))
        elif hasattr(message.data, '__iter__'):
            for x in message.data:
                yield message.reply(*youtube(x))

    @command
    def pdf(self, message):
        if isinstance(message.data, str):
            urls = message.data.split()
            if urls:
                return message.reply(*read_pdf_metadata(urls[0]))


    @regex(r"(?:https?://www|https?://|www)")
    def url(self, message):
        if message.text[0] not in "!#.$%" and message.params.lower() != "#kentcs":
            links = set()

            links.update(linkregex.findall(message.text))
            for link in links:
                hasresponded = False

                if not link.startswith("http"):
                    link = "http://" + link

                for pattern, handler in websitehandlers.items():
                    if re.search(pattern, link):
                        data, text = handler(link)
                        yield message.reply(data, text)
                        hasresponded = True

                if not hasresponded:
                    head = requests.head(link, timeout=5)
                    contentstats = ""
                    if "content-type" in head.headers:
                        contentstats += head.headers["content-type"]
                    else:
                        contentstats += "Unknown type"
                    if "content-length" in head.headers:
                        try:
                            length = size(int(head.headers["content-length"]))
                        except:
                            length = "0B"
                        contentstats += "; " + length
                    if "html" in contentstats.lower():
                        page = requests.get(link, headers=headers, stream=True)

                        parse = TitleHTMLParser(convert_charrefs=True)

                        parse.feed(page.content.decode())
                        if parse.title:
                            yield message.reply("Title: " + parse.title.strip())
                            hasresponded = True

                    if contentstats and not hasresponded:
                        yield message.reply("[%s]" % contentstats)







