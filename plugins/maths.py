from wrappers import *
from plugins.stuff.countdownsolver import solve, solve_best
from Message import Message
from collections import namedtuple, defaultdict, Counter, ChainMap
from random import randint, sample
import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}



def eval_expr(expr):
    try:
        return eval_(ast.parse(expr, mode='eval').body, locals)
    except EOFError:
        raise Exception("something is not quite right with your input...")


def eval_(node, locals = dict()):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left, locals), eval_(node.right, locals))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand, locals))
    else:
        if node:
            raise Exception(ast.dump(node))



Game = namedtuple('game', ['target', 'numbers', 'closest', 'bestuser', 'startedby', 'startedat'])


@plugin
class countdown:
    def __init__(self):
        self.games = defaultdict(dict)
        self.big = [25, 50, 75, 100]
        self.small = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10]

    @command("cd")
    @command("solve")
    @command("countdown")
    def cd_solve(self, message):
        target, *numbers = [int(x) for x in message.text.split()]
        if len(numbers) > 6:
            raise Exception("too many numbers")
        expr, value = solve(target, numbers)
        if value == target:
            yield message.reply("Solution: " + expr + " = " + str(target))
        else:
            yield message.reply("closest: " + expr + " = " + str(value))


    @command("cdb")
    @command("cdbest")
    @command("solvebest")
    def cd_solve_best(self, message):
        target, *numbers = [int(x) for x in message.text.split()]
        expr, value = solve_best(target, numbers)
        if value == target:
            yield message.reply("Best solution: " + expr + " = " + str(target))
        else:
            yield message.reply("closest: " + expr + " = " + str(value))

    @command("cdn")
    @command("cdnewgame")
    def newgame(self, message):
        if not self.games[message.params]:
            target = randint(0, 999)
            numbers = sample(self.big, 2) + sample(self.small, 4)
            user = message.nick
            game = Game(target, numbers, None, None, user, message.timestamp)
            self.games[message.params] = game
            yield message.reply('Target is ' + str(target) + ' and the numbers are: ' +
                                ", ".join([str(x) for x in numbers]))
        else:
            yield message.reply('Game in progress, target is ' +
                                str(self.games[message.params].target) + ' and the numbers are: ' +
                                ", ".join([str(x) for x in self.games[message.params].numbers]))


    @command("cdg")
    @command("cdgiveup")
    def giveup(self, message):
        if self.games[message.params]:
            yield message.reply("attempting to solve...")
            target = self.games[message.params].target
            numbers = self.games[message.params].numbers
            expr, value = solve(target, numbers)
            if value == target:
                yield message.reply("Solution: " + expr + " = " + str(target))
            else:
                yield message.reply("closest: " + expr + " = " + str(value))
            del self.games[message.params]
        else:
            yield message.reply("no game running")

    @command("cda")
    @command("cdanswer")
    def answer(self, message):
        if self.games[message.params]:
            numbersused = Counter(map(float, re.findall("[0-9]+", message.text)))
            numberset = Counter(self.games[message.params].numbers)
            if not numbersused - numberset:
                if int(eval_expr(message.text.strip())) == self.games[message.params].target:
                    yield message.reply("Correct! ten points to " + message.nick + "dor (in theory...)")
                    del self.games[message.params]
                elif abs(eval_expr(message.text.strip()) - self.games[message.params].target) < 10:
                    no = abs(eval_expr(message.text.strip()) - self.games[message.params].target)
                    yield message.reply(
                        str(no) + " away! " + str(10 - no) + " points to " + message.nick + "dor (in theory...)")
                else:
                    yield message.reply("Incorrect! your answer equals " + str(eval_expr(message.text.strip())))
            else:
                raise Exception("incorrect numbers used")
        else:
            raise Exception("incorrect numbers used")
