from random import shuffle
from itertools import cycle
from collections import defaultdict

from wrappers import *
from Message import Message
import time


def chunk_by_key(iterable, keyfunc):
    i = iter(iterable)

    current_val = next(i, None)
    if current_val is not None:
        sub_key, current_key = [keyfunc(current_val)] * 2
        current_sub = list()
        while current_val is not None:
            current_key = keyfunc(current_val)
            if current_key == sub_key:
                current_sub.append(current_val)
            else:
                yield current_sub
                current_sub = list()
                current_sub.append(current_val)
                sub_key = current_key
            current_val = next(i, None)
        yield current_sub


@plugin
class Cheat:
    def __init__(self):
        self.games = defaultdict(lambda: defaultdict(CheatGame))
        self.playersingames = defaultdict(lambda: defaultdict(set))

    def getplayergamecommands(self, message, partof=False):
        if message.text and message.text[0] == "#":
            channel = message.text.strip().split()[0]
            # print(channel)
            # print(self.games[message.server])
            if channel in self.games.get(message.server, {}):
                game = self.games[message.server][channel]
                print(game.players)
                player = game.players.get(message.nick, None)
                print(player)
                if partof and player is None:
                    raise Exception("not part of that game")
                return player, game, " ".join(message.text.strip().split()[1:]), channel
            else:
                raise Exception("no such game")
        elif message.params == message.nick:
            noofgames = len(self.playersingames.get(message.server, {}).get(message.nick, []))
            if noofgames == 1:
                channel = list(self.playersingames[message.server][message.nick])[0]
                game = self.games[message.server][channel]
                player = game.players[message.nick]
                return player, game, message.text, channel
            elif noofgames > 1:
                raise Exception("specify game")
            else:
                raise Exception("not part of any game")
        else:
            game = self.games.get(message.server, {}).get(message.params, None)
            if game:
                player = game.players.get(message.nick, None)
                if partof and player is None:
                    print(game)
                    print(game.players)
                    raise Exception("not part of that game")
                return player, game, message.text, message.params
            else:
                raise Exception("no such game")


    @command
    def place(self, message):
        player, game, args, channel = self.getplayergamecommands(message, partof=True)
        try:
            val = int(args)
        except:
            print(message)
            raise Exception("invalid arg")
        print(game.currentplayer)
        if message.nick == game.currentplayer:
            result = player.place(args)
            if result:
                response = "{} has successfully put down all of thier cards! GAME OVER".format(game.mostrecentplayer)
            else:
                response = "Player {} has placed {} {} {}".format(message.nick, len(player), val,
                                                              "\3{0[0]},{0[1]}{1}{2}\3 ".format(backcolour, backstr * 2,
                                                                                                backstr) * min(len(player),5))
            yield Message(text=response, params=channel, command="PRIVMSG", server=message.server)
        else:
            yield Message(params=message.nick, command="PRIVMSG", server=message.server,
                          text="Game: {}: it is not your turn, it is currently {}'s turn".format(channel,
                                                                                                 game.currentplayer))

    @command(pipable=False)
    def joingame(self, message):
        if message.params != message.nick:
            if message.params not in self.games[message.server]:
                text = 'Starting game for this channel, use command {}ready when you would like to begin. needs at least two people to play'.format(self.bot.command_char)
                self.games[message.server][message.params].addplayer(message.nick)
                self.playersingames[message.server][message.nick].add(message.params)
            elif self.games[message.server][message.params].starting:
                text = "joined the game!"
                self.games[message.server][message.params].addplayer(message.nick)
                self.playersingames[message.server][message.nick].add(message.params)
            elif self.games[message.server][message.params].started:
                raise Exception("game in progress")
            else:
                self.games[message.server][message.params].addplayer(message.nick)
                self.playersingames[message.server][message.nick].add(message.params)
                text = 'joining game for this channel, use command {}ready when you would like to begin. There are currently {} players.'.format(self.bot.command_char, len(self.games[message.server][message.params].players))

            if message.text == "ready":
                yield from self.ready(message.reply(message.params))
            else:
                yield message.reply(text)


    @command
    def hand(self, message):
        player, game, args, channel = self.getplayergamecommands(message, partof=True)
        print(player.hand.cards)
        hand = list(
            chunk_by_key(sorted(player.hand.cards, key=lambda card: (card.val, card.suit)), lambda card: card.val))
        fst = []
        while sum([len(group) for group in hand]) > 34:
            fst = hand.pop() + [""] + fst

        prefix = "Game {}: you have {} cards: ".format(channel, len(player))
        hand = "  ".join([" ".join(map(str, group)) for group in hand])

        yield message.reply(prefix + hand)
        if fst:
            fst = " ".join(map(str, fst))
            yield message.reply(len(prefix) * " " + fst)

    @command
    def ready(self, message):
        player, game, args, channel = self.getplayergamecommands(message, partof=True)

        player.ready = True
        if not game.starting:
            notready = [nick for nick, player__ in game.players.items() if not player__.ready]

            if len(game.players) < 2:
                    yield message.reply("you need one more person to play!")
            elif not len(notready):
                yield message.reply("game will start in 10 seconds, anybody else who wants to play should join quick!")
                game.starting = True
                time.sleep(10)


                game.start()
                yield message.reply("game starting! now dealing out your cards. {} is to start!".format(game.currentplayer))
                print(game.players.items())
                for nick, player_ in game.players.items():
                    hand = list(chunk_by_key(sorted(player_.hand.cards, key=lambda card: (card.val, card.suit)),
                                             lambda card: card.val))
                    fst = []
                    while sum([len(group) for group in hand]) > 34:
                        fst = hand.pop() + [""] + fst

                    prefix = "Game {}: have {} cards: ".format(channel, len(player_))
                    hand = "  ".join([" ".join(map(str, group)) for group in hand])

                    yield Message(params=nick, command="PRIVMSG", server=message.server, text=prefix + hand)
                    if fst:
                        fst = " ".join(map(str, fst))
                        yield Message(params=nick, command="PRIVMSG", server=message.server, text=len(prefix) * " " + fst)

            else:
                yield message.reply("Player {} is ready! {} needs to ready up for the game to begin"
                                    .format(message.nick, " and ".join((", ".join(notready[:-1]), notready[-1])
                                                                       if len(notready) > 1 else (notready[-1],))))

    @command
    def cheat(self, message):
        player, game, args, channel = self.getplayergamecommands(message, partof=True)
        result = player.cheat()
        if result:
            picker = game.mostrecentplayer
        else:
            picker = message.nick
        yield Message(
            text="Player {} has called cheat on {}!".format(message.nick, game.mostrecentplayer) +
                 (' The "{}" cards were actually {} {} picks up the pile!'
                  .format(game.mostrecentval, " ".join(map(str, game.mostrecent[:5] + ["..."]
                                                           if len(game.mostrecent) > 5 else game.mostrecent)), picker)),
            params=channel, command="PRIVMSG", server=message.server)
        if result:
            yield Message(params=channel, command="PRIVMSG", server=message.server, text="{} has successfully put down"
            "all of thier cards! GAME OVER")

    @command
    def select(self, message):
        pass

    @command
    def concede(self, message):
        pass


class CheatPlayer:
    def __init__(self, game):
        self.hand = Hand()
        self.selected = set()
        self.game = game
        self.ready = False

    def __len__(self):
        return len(self.hand)

    def select(self, val=None, suit=None):
        cards = self.hand.findall(val, suit)
        card = next(filter(lambda x: x not in self.selected, cards), None)
        if card:
            self.selected.add(card)

    def unselect(self, val=None, suit=None):
        cards = self.hand.findall(val, suit)
        card = next(filter(lambda x: x in self.selected, cards), None)
        if card:
            self.selected.remove(card)

    def cheat(self):
        result = self.game.cheat()
        if not result:
            self.hand.pickup(*self.game.pile.get())
        return result

    def place(self, val):
        if not self.selected:
            l = len(self.hand)
            self.game.place(self.hand.cards, val)
            self.hand = Hand()
            return l
        l = len(self.selected)
        self.game.place(self.selected, val)
        for card in self.selected:
            self.hand.remove(card)
        self.selected = set()
        return l


class CheatGame:
    def __init__(self):
        self.players = {}
        self.out = set()
        self.pile = Pile()

        self.currentplayer = ""

        self.mostrecent = []
        self.mostrecentval = 0
        self.mostrecentplayer = ""

        self.order = []
        self.deck = Deck(jokers=True)

        self.starting = False
        self.started = False

    def addplayer(self, player):
        self.players[player] = CheatPlayer(self)

    def removeplayer(self, player):
        del self.players[player]

    def start(self):
        self.started = True
        self.order = list(self.players.keys())
        shuffle(self.order)
        self.order = cycle(self.order)
        self.deck.shuffle()
        for card in self.deck:
            self.players[next(self.order)].hand.pickup(card)
        self.currentplayer = next(self.order)

    def checkwinner(self):
        if len(self.players[self.mostrecentplayer].hand) == 0:
            self.out.add(self.mostrecentplayer)
            return True
        return False

    def place(self, cards, val):
        self.pile.put(*cards)
        self.mostrecent = list(cards)
        self.mostrecentval = val
        self.nextplayer()
        return self.checkwinner()

    def cheat(self):
        result = all(map(lambda card: card.val == self.mostrecentval or card.val == 0, self.mostrecent))
        if result:
            self.players[self.mostrecentplayer].hand.pickup(*self.pile.get())
            return True
        else:
            return False

    def nextplayer(self):
        self.mostrecentplayer = self.currentplayer
        for x in self.order:
            if x == self.currentplayer:
                raise Exception("NO MORE PLAYERS LEFT")
            elif x in self.out:
                continue
            else:
                self.currentplayer = x


class Deck:
    def __init__(self, decks=1, jokers=False):
        self.deck = []
        if jokers:
            self.deck.append(Card(0, 5))
            self.deck.append(Card(0, 6))
        for d in range(decks):
            for i in range(1, 5):
                for j in range(1, 14):
                    self.deck.append(Card(j, i))

    def deal(self, no=1):
        to_return = []
        for i in range(no):
            to_return.append(self.deck.pop())
        return to_return

    def shuffle(self):
        shuffle(self.deck)

    def __iter__(self):
        while self.deck:
            yield self.deck.pop()


class Pile:
    def __init__(self, cards=None):
        self.cards = cards or []

    def get(self, no=0):
        to_return = self.cards[-no:][::-1]
        del self.cards[-no:]
        return to_return

    def put(self, *cards):
        for card in cards:
            self.cards.append(card)


class Hand:
    def __init__(self, cards=None):
        self.cards = cards or []

    def __str__(self):
        return " ".join(map(str, sorted(self.cards, key=lambda card: (card.val, card.suit))))

    def backs(self):
        return ("\3{0[0]},{0[1]}{1}{2}\3 ".format(backcolour, backstr * 2, backstr) * len(self.cards)) or ""

    def __len__(self):
        return len(self.cards)

    def find(self, val=None, suit=None):
        return next(filter(lambda x: val is None or x.val == val and suit is None or x.suit == suit, self.cards), None)

    def findall(self, val=None, suit=None):
        return filter(lambda x: val is None or x.val == val and suit is None or x.suit == suit, self.cards)

    def remove(self, x):
        return self.cards.remove(x)

    def sort(self, bysuits=False):
        if bysuits:
            self.cards = sorted(self.cards, key=lambda card: (card.suit, card.val))
        else:
            self.cards = sorted(self.cards, key=lambda card: (card.val, card.suit))

    def pickup(self, *cards, sort=False, bysuits=False):
        for card in cards:
            self.cards.append(card)
        if sort:
            self.sort(bysuits)


backcolour = (0, 5)
backstr = "▒"

suitcolours = {
    1: (5, 15),
    2: (5, 15),
    3: (1, 15),
    4: (1, 15),
    5: (5, 15),
    6: (1, 15),
}

suits = {
    1: "♥",
    2: "♦",
    3: "♣",
    4: "♠",
    5: "",
    6: "",
}

cardvals = {
    0: "JOK",
    1: "A\xa0",
    2: "2\xa0",
    3: "3\xa0",
    4: "4\xa0",
    5: "5\xa0",
    6: "6\xa0",
    7: "7\xa0",
    8: "8\xa0",
    9: "9\xa0",
    10: "10",
    11: "J\xa0",
    12: "Q\xa0",
    13: "K\xa0",
}


class Card:
    def __init__(self, val, suit):
        self.val = val
        self.suit = suit

    def __str__(self):
        return "\3{0[0]},{0[1]}{1}{2}\3".format(suitcolours[self.suit], cardvals[self.val], suits[self.suit])

    def __eq__(self, other):
        return self.suit == other.suit and self.val == other.val