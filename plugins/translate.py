import urllib.request
import urllib.error
import urllib.parse
import json

from wrappers import *


@plugin(desc="google translator")
class Google():

    def __init__(self):
            self.param = re.compile("^(?: *(\w+)?:(\w+)?)(.*)")
            
            self.lang_in = {
                "afrikaans": "af",  "albanian": "sq", "arabic": "ar", "armenian": "hy", "azerbaijani": "az",
                "basque": "eu", "belarusian": "be", "bengali": "bn", "bulgarian": "bg", "catalan": "ca",
                "chinese": "zh-CN", "croatian": "hr", "czech": "cs", "danish": "da", "dutch": "nl", "english": "en",
                "estonian": "et", "esperanto": "eo", "filipino": "tl", "finnish": "fi", "french": "fr",
                "galician": "gl", "georgian": "ka", "german": "de", "greek": "el", "gujarati": "gu", "hebrew": "iw",
                "hindi": "hi", "hungarian": "hu", "icelandic": "is", "indonesian": "id", "irish" : "ga",
                "italian": "it", "japanese": "ja", "korean": "ko", "latin": "la", "latvian": "lv", "lithuanian": "lt",
                "macedonian": "mk", "malay": "ms", "maltese": "mt", "norwegian": "no", "persian": "fa", "polish": "pl",
                "portuguese": "pt", "romanian": "ro", "russian": "ru", "serbian": "sr", "slovak": "sk",
                "slovenian": "sl", "spanish": "es", "swahili": "sw", "swedish": "sv", "thai": "th", "turkish": "tr",
                "ukrainian" : "uk", "vietnamese": "vi", "welsh": "cy", "yiddish": "yi", "xhosa": "xh"}
        
            self.lang_out = dict((value,key) for (key, value) in list(self.lang_in.items()))

    @command("t")
    def translate(self, message):
        """t [from:to] text -> attempts to translate the text from the specified language to the other specified language. any unspecified language will be assumed to be english"""
        lang, *tr = self.parse_and_translate(message.text)
        return message.reply(", ".join(tr), lang + ", ".join(tr))

    def parse_and_translate(self, text, verbose=True):
        match = self.param.match(text.lower())
        lang_from, lang_to, text = match.groups() if match else (None, None, text)
        
        if not lang_from:
            lang_from_key = "auto"
        elif lang_from in self.lang_in.keys():
            lang_from_key = self.lang_in[lang_from]
        elif lang_from in self.lang_in.values():
            lang_from_key = lang_from
        else:
            raise Exception("language: {} not recognised".format(lang_from))
            
        if not lang_to:
            lang_to_key = "en"
        elif lang_to in self.lang_in.keys():
            lang_to_key = self.lang_in[lang_to]
        elif lang_to in self.lang_in.values():
            lang_to_key = lang_to
        else:
            raise Exception("language: {} not recognised".format(lang_to))
            
        return self.translate_language(text, lang_from_key, lang_to_key, verbose)
            
    def translate_language(self, text, source_lang="auto", dest_lang="en", verbose=True):
        translate_params = {"client": "xxxxxxx", "text": text, "hl": "en", "sl": source_lang,
                            "tl": dest_lang, "ie": "UTF-8", "oe": "UTF-8"}
        url_translate = "http://translate.google.com/translate_a/t?"
        headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        url = url_translate + urllib.parse.urlencode(translate_params)
        req = urllib.request.Request(url, None, headers)
        #true = "true"
        response = json.loads(urllib.request.urlopen(req).read().decode())
        lang = self.lang_out[response["src"]] if response["src"] in self.lang_out else response["src"]
        lang = lang + " to " + self.lang_out[dest_lang] + ": "
        if verbose and "dict" in response and len(response["dict"][0]["terms"]) > 1:
            return [lang] + response["dict"][0]["terms"]
        elif verbose:
            return (lang, "".join([x["trans"] for x in response["sentences"]]))
        else:
            return "".join([x["trans"] for x in response["sentences"]])
        
@plugin
class morse:
    
    morsecodes = {
        "a" : ".-",
        "b" : "-...",
        "c" : "-.-.",
        "d" : "-..",
        "e" : ".",
        "f" : "..-.",
        "g" : "--.",
        "h" : "....",
        "i" : "..",
        "j" : ".---",
        "k" : "-.-",
        "l" : ".-..",
        "m" : "--",
        "n" : "-.",
        "o" : "---",
        "p" : ".--.",
        "q" : "--.-",
        "r" : ".-.",
        "s" : "...",
        "t" : "-",
        "u" : "..-",
        "v" : "...-",
        "w" : ".--",
        "x" : "-..-",
        "y" : "-.--",
        "z" : "--..",
        "0" : "-----",
        "1" : ".----",
        "2" : "..---",
        "3" : "...--",
        "4" : "....-",
        "5" : ".....",
        "6" : "-....",
        "7" : "--...",
        "8" : "---..",
        "9" : "----.",
        "." : ".-.-.-",
        "," : "--..--",
        "?" : "..--..",
        "'" : ".----.",
        "!" : "-.-.--",
        "/" : "-..-.",
        "(" : "-.--.",
        ")" : "-.--.-",
        "&" : ".-...",
        ":" : "---...",
        ";" : "-.-.-.",
        "=" : "-...-",
        "+" : ".-.-.",
        "-" : "-....-",
        "_" : "..--.-",
        '"' : ".-..-.",
        "$" : "...-..-",
        "@" : ".--.-.",
        " " : "/"}

    umorsecodes = dict([(value,key) for (key, value) in list(morsecodes.items())])

    @command
    def morse(self, message):
        ret = []
        for char in message.data:
            if char in self.morsecodes:
                ret.append(self.morsecodes[char])
            else:
                ret.append("?")
        return message.reply(" ".join(ret))
    
    @command
    def umorse(self, message):
        ret = []
        textl = message.data.split(" ")
        for char in textl:
            if char in self.umorsecodes:
                ret.append(self.umorsecodes[char])
            else:
                ret.append("?")

        return message.reply("".join(ret))