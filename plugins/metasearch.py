from wrappers import *
import requests
from lxml import html
import urllib.parse
from collections import defaultdict
from itertools import zip_longest
import re

def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


@plugin
class searcher:


    def __init__(self):
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13'}

        self.websitehandlers = {
            r".*\.wikipedia\.org": self.wikipediaparse,
            r"www\.urbandictionary\.com\/define": self.urbandictionaryparse,
        }

    @command("g", simple=True)
    def search(self, message):
        query = "http://www.google.co.uk/search?q=" + urllib.parse.quote(message.data)
        print(query)


        page = requests.get(query, headers=self.headers)
        print(page.text, file=open("temp.html","w+"))
        tree = html.fromstring(page.text)
        print(tree)


        result = tree.xpath('(//*[@class="r"])[1]//text()')
        resultlink = tree.xpath('(//*[@class="r"])[1]//@href')
        print(result, resultlink)

        if resultlink:
            resultlink = urllib.parse.parse_qs(urllib.parse.urlparse("test.com"+resultlink[0]).query)["q"][0] if resultlink[0].startswith("/url?") else resultlink[0]
            print(resultlink)

        weather = tree.xpath('//div[@class="e"][1]')
        if weather:
            *title , weather, source  = weather[0].xpath('./h3//text() | ./table')
            weather = "".join(weather.xpath('./tr[1]/td[2]/span/text() | ./tr[3]/td/text() | ./tr[4]/td//text() | ./tr[5]/td[1]/text()'))
            weather = "".join(title) +" "+ weather



        definitionsets = list(grouper(tree.xpath('//li[@class="g"][1]/div[not(@class="e")]/h3 | //li[@class="g"][1]/div[not(@class="e")]/table'), 2))

        definitions = defaultdict(list)

        for h3, table in definitionsets:
            definitiontypes = list(grouper(table.xpath("./tr/td/div/text() | ./tr/td/ol"), 2))
            for type, ol in definitiontypes:
                dfns = ol.xpath("./li/text()")
                definitions[type].extend(dfns)


        if definitions:
            for dfntype, dfns in definitions.items():
                yield message.reply(dfntype +": " + " ".join(dfns[:1]))
        elif weather:
            yield message.reply(weather)
        else:
            responded = False
            for pattern, handler in self.websitehandlers.items():
                if resultlink and re.search(pattern, resultlink):
                    print("MATCH")
                    for response in handler(resultlink):
                        yield message.reply(response)
                        responded = True
                        break
            if not responded:
                if resultlink:
                    yield message.reply("top result: %s %s" % ("".join(result), resultlink))
                elif result:
                    yield message.reply("result: %s" % "".join(result))




    def wikipediaparse(self, url):
        page = requests.get(url, headers=self.headers)
        tree = html.fromstring(page.text)
        yield "".join(tree.xpath('//*[@id="mw-content-text"]/p[1]/*[not(name()="sup")]//text() | //*[@id="mw-content-text"]/p[1]/text()'))


    def urbandictionaryparse(self, url):
        page = requests.get(url, headers=self.headers)
        tree = html.fromstring(page.text)
        for defpanel in tree.xpath('//div[@class="def-panel"]'):
            meaning = "".join(defpanel.xpath('./div[@class="meaning"]/text()'))
            example = "".join(defpanel.xpath('./div[@class="example"]/text()'))
            yield "Urban Dictionary: " + "".join(meaning) + (' "%s"' % example) if len(example) < 100 else ""





    #@command("w")
    def wsearch(self, message):
        query = "http://www.google.co.uk/search?q=what+is+" + urllib.parse.quote(message.data)
        headers = {'user-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Version/3.1 Safari/525.13'}

        page = requests.get(query, headers=headers, stream=True)
        print(page.text, file=open("temp.html","w+"))
        tree = html.fromstring(page.text)
        print(tree)


        definitions = tree.xpath('//li[@style="list-style-type:decimal"]/text()')

        print(definitions)

