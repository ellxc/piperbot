from wrappers import *
import re, collections


@plugin
class sp:
    def __init__(self):
        wordlists = ['/usr/share/dict/british-english-insane', '/usr/share/dict/british-english-huge', 
                     '/usr/share/dict/british-english-large', '/usr/share/dict/british-english',
                      '/usr/share/dict/british-english-small']
        self.NWORDS = collections.Counter()
        for filename in wordlists:
            try:
                with open(filename) as file:
                    self.NWORDS.update(re.findall('\w+', file.read()))
            except:
                pass
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.reg = re.compile(r"(\S+)\[sp\]")

    def edits1(self, word):
        s = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes    = [a + b[1:] for a, b in s if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in s if len(b)>1]
        replaces   = [a + c + b[1:] for a, b in s for c in self.alphabet if b]
        inserts    = [a + c + b     for a, b in s for c in self.alphabet]
        return set(deletes + transposes + replaces + inserts)

    def known_edits2(self, word):
        return set(e2 for e1 in self.edits1(word) for e2 in self.edits1(e1) if e2 in self.NWORDS)

    def known(self, words):
        return set(w for w in words if w in self.NWORDS)

    def correct(self, word):
        candidates = self.known([word]) or self.known(self.edits1(word)) or self.known_edits2(word) or [word]
        return max(candidates, key=self.NWORDS.get)

    @command("sp")
    def sp(self, message):
        ret = []
        for word in message.data.split():
            ret.append(self.correct(word))
        return message.reply(" ".join(ret))

    @regex(r".*\S+\[sp\]")
    def regsp(self, message):
        return message.reply(self.reg.sub(lambda obj: self.correct(obj.group(1)), message.text))
