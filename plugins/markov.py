import random
from collections import deque

from wrappers import *
import pymongo
from bson.code import Code


class mongomarkov():
    def __init__(self,dbname="markov"):
        self.con = pymongo.MongoClient()
        self.db = self.con[dbname]
        self.links = self.db.links
        self.start = "\0"
        self.end = "\1"
        
        self.mapper = Code("""function () {
                                emit(this.next,this.count*Math.random());
                            }""")
                            
        self.reducer = Code("""function (key, values) {
                                return values[0];
                            }""")
         
    def putline(self,line):
        sequence = [self.start]*2+line.split()+[self.end]*2
        for i in range(len(sequence)-(2)):
            prev = sequence[i]
            current = sequence[i+1]
            next = sequence[i+2]
            self.put(prev,current,next)

    def put(self,previous,current,next):
        self.links.update({"prev":previous,"curr":current,"next":next},{"$inc":{"count" : 1}},upsert=True)
                    
    def get_next(self,previous,current): # get the next word based on the current and previous words
        return sorted(self.links.find({"prev":previous,"curr":current}),key=lambda w: w["count"]*random.randint(0,100))[0]["next"]
        
    
    def get_previous(self,current,next): # get the previous word based on the current and next words
        return sorted(self.links.find({"next":next,"curr":current}),key=lambda w: w["count"]*random.randint(0,100))[0]["prev"]
        
    def get(self,current): # get the next and previous word based on the current word
        nodes = sorted(self.links.find({"curr":current}),key=lambda w: w["count"]*random.randint(0,100))
        if not nodes: raise Exception( '"'+current + '" not in DB')
        else: node = nodes[0]
        previous = node["prev"]
        next = node["next"]
        return previous,next
        
        
    def make_line_from(self,word):
        previous, next = self.get(word)
        sequence = deque([previous,word,next])
        
        while sequence[-1] not in [self.end,None]:
            sequence.append(self.get_next(sequence[-2],sequence[-1]))
        while sequence[0] not in [self.start,None]:
            sequence.appendleft(self.get_previous(sequence[0],sequence[1]))
        return " ".join(list(sequence)[1:-1])
         
        
    def make_line(self):
        sequence = [self.start]*(2)
        while sequence[-1] not in [self.end,None]:
            sequence.append(self.get_next(sequence[-2],sequence[-1]))
        return " ".join(sequence[2:-1])

@plugin
class markov:

    @on_load
    def init(self):
        self.chain = mongomarkov()
    
    @command("talk")
    def talk(self,message):
        if message.text.startswith("about ") and len(message.text.split()) > 1:
            about = message.text.split()[1]
            line = self.chain.make_line_from(about)
        elif  message.text.startswith("to ") and len(message.text.split()) > 1:
            nick = message.text.split()[1]
            line = self.chain.make_line_from(nick + ":")
        else:
            line = self.chain.make_line()
        return message.reply(line)
        
        
    @command("clear", adminonly=True)
    def clear(self, message):
        self.chain.links.remove({})
        
    @trigger(lambda message, bot: message.command == "PRIVMSG" and bot.servers[message.server].nick in message.text and message.nick not in ["CirnoX"] and message.text[0] not in "!#%$.")
    def mention(self, message):
        if message.text.startswith(self.bot.servers[message.server].nick+":"):
            try:
                return message.reply(self.chain.make_line_from(message.nick + ":"))
            except:
                return message.reply(self.chain.make_line())
        else:
            return message.reply(self.chain.make_line())

    @event("PRIVMSG")
    def add(self, message):
        if message.text and message.text[0] not in "!#%$.":
            self.chain.putline(message.text)
