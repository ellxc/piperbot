import ast
import math
from collections import OrderedDict, defaultdict, ChainMap
import pickle
import datetime
#from random import random, uniform, triangular, randint, choice, randrange, sample, shuffle, getrandbits
import random
from wrappers import *
import pymongo
import sys
import json
import re
import traceback

boolops = {
    ast.And: all,
    ast.Or: any,
}

binops = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a ** b,
    ast.LShift: lambda a, b: a << b,
    ast.RShift: lambda a, b: a >> b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
    ast.BitAnd: lambda a, b: a & b,
    ast.FloorDiv: lambda a, b: a // b,
}

unaryops = {
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: not a,
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
}

compares = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

slices = {
    ast.Slice: lambda env, lower, upper, step, value_:
    eval_expr(value_, env)[slice(eval_expr(lower, env), eval_expr(upper, env), eval_expr(step, env))],
    ast.Index: lambda env, value, expr=None, value_=None:
    expr[eval_expr(value, env)] if expr is not None else eval_expr(value_, env)[eval_expr(value, env)],
}

exprs = {
    ast.BoolOp: lambda env, op, values: boolops[type(op)](eval_expr(value, env) for value in values),
    ast.BinOp: lambda env, op, left, right: binops[type(op)](eval_expr(left, env), eval_expr(right, env)),
    ast.UnaryOp: lambda env, op, operand: unaryops[type(op)](eval_expr(operand, env)),
    ast.Lambda: lambda env, args, body: lambda_(args, body, env),
    ast.IfExp: lambda env, test, body, orelse: eval_expr(body, env) if eval_expr(test, env) else eval_expr(orelse, env),
    ast.Dict: lambda env, keys, values: {eval_expr(key, env):
                                             eval_expr(value, env) for key, value in zip(keys, values)},
    ast.Set: lambda env, elts: {eval_expr(elt, env) for elt in elts},
    ast.ListComp: lambda env, elt, generators: [eval_expr(elt, genenv) for genenv in generate(generators, env)],
    ast.SetComp: lambda env, elt, generators: {eval_expr(elt, genenv) for genenv in generate(generators, env)},
    ast.DictComp: lambda env, key, value, generators: {eval_expr(key, genenv): eval_expr(value, genenv) for genenv in
                                                       generate(generators, env)},
    ast.Compare: lambda env, left, ops, comparators: compare_(left, ops, comparators, env),
    ast.Call: lambda env, func, args, starargs, keywords, kwargs: call_(func, args, starargs, keywords, kwargs, env),
    ast.Num: lambda env, n: n,
    ast.Str: lambda env, s: s,
    ast.Subscript: lambda env, ctx, value, slice: #raise_(ast.dump(slice)),
    slices[type(slice)](value_=value, env=env, **dict(ast.iter_fields(slice))),
    ast.Name: lambda env, ctx, id: env[id],
    ast.List: lambda env, ctx, elts: list(eval_expr(elt, env) for elt in elts),
    ast.Tuple: lambda env, ctx, elts: tuple(eval_expr(elt, env) for elt in elts),
    ast.NameConstant: lambda env, value: value,
    ast.Attribute: lambda env, value, attr, ctx:
    (getattr(eval_expr(value, env), attr) if isinstance(value, ast.Attribute) else getattr(eval_expr(value, env), attr))
    if not attr.startswith("__") else raise_("access to private fields is restricted"),
}

str_boolops = {
    ast.And: " and ",
    ast.Or: " or ",
}

str_binops = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.Div: "/",
    ast.Mod: "%",
    ast.Pow: "**",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.BitOr: "|",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.FloorDiv: "//",
}

str_unaryops = {
    ast.Invert: "~",
    ast.Not: "not ",
    ast.UAdd: "+",
    ast.USub: "-",
}

str_compares = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Is: " is ",
    ast.IsNot: " is not ",
    ast.In: " in ",
    ast.NotIn: " not in ",
}

str_slices = {
    ast.Slice: lambda expr, lower, upper, step, value_ = None: str(expr) + "[" + ast_to_string(lower) + ((":" + ast_to_string(upper) +
                                                                                           ((":" + ast_to_string(step))
                                                                                            if step != 1 else ""))
                                                                                          if upper else "") + "]",
    ast.Index: lambda value, expr=None, value_=None:
    (str(expr) + "[" + ast_to_string(value) + "]") if expr is not None else (
        ast_to_string(value_) + "[" + ast_to_string(value) + "]"),
}

str_exprs = {
    ast.BoolOp: lambda op, values: "(" + str_boolops[type(op)].join(map(ast_to_string, values)) + ")",
    ast.BinOp: lambda op, left, right: "(" + ast_to_string(left) + str_binops[type(op)] + ast_to_string(right) + ")",
    ast.UnaryOp: lambda op, operand: str_unaryops[type(op)] + ast_to_string(operand),
    ast.Lambda: lambda args, body: "lambda " + ",".join(
        [x.arg for y in dict(ast.iter_fields(args)).values() if y for x in y]) + ": " + ast_to_string(body),
    ast.IfExp: lambda test, body, orelse: ast_to_string(body) + " if " + ast_to_string(test) + " else " + ast_to_string(
        orelse),
    ast.Dict: lambda keys, values: "{" + ", ".join([ast_to_string(key) + ":" +
                                                    ast_to_string(value) for key, value in zip(keys, values)]) + "}",
    ast.Set: lambda elts: "{" + ",".join([ast_to_string(elt) for elt in elts]) + "}",
    ast.ListComp: lambda elt, generators: "list comp",
    # "[" + ",".join([eval_expr(elt, genenv) for genenv in generate(generators)]) +"]",
    ast.SetComp: lambda elt, generators: "set comp",
    # {eval_expr(elt, genenv) for genenv in generate(generators, env)},
    ast.DictComp: lambda key, value, generators: "dict comp",
    # {eval_expr(key, genenv): eval_expr(value, genenv) for genenv in generate(generators, env)},
    ast.Compare: lambda left, ops, comparators: ast_to_string(left) + "".join(
        [str_compares[type(op)] + ast_to_string(compar) for op, compar in zip(ops, comparators)]),
    ast.Call: lambda func, args, starargs, keywords, kwargs:
    ast_to_string(func) + "(" + ",".join(
        (list(map(ast_to_string, args)) if args else []) + (list(map(ast_to_string, starargs)) if starargs else []) + [
            a + "=" + ast_to_string(b) for a, b in [(keyword.arg, keyword.value) for keyword in keywords]]) + ")",
    # + kwargs]),
    ast.Num: lambda n: str(n),
    ast.Str: lambda s: "'" + s + "'",
    ast.Subscript: lambda ctx, value, slice:
    str_slices[type(slice)](value_=value, **dict(ast.iter_fields(slice))),
    ast.Name: lambda ctx, id: id,
    ast.List: lambda ctx, elts: "[" + ",".join(map(ast_to_string, elts)) + "]",
    ast.Tuple: lambda ctx, elts: "(" + ",".join([ast_to_string(elt) for elt in elts]) + ")",
    ast.NameConstant: lambda value: str(value),
    ast.Attribute: lambda value, attr, ctx: value + "." + attr,
}


def ast_to_string(node):
    if type(node) in str_exprs:
        try:
            return str_exprs[type(node)](**dict(ast.iter_fields(node)))
        except Exception as e:
            raise e
            return str(type(node))
    else:
        try:
            raise Exception(ast.dump(node))
        except TypeError:
            raise Exception(node)



globalenv = {
    "maxint": sys.maxsize,
    'len': len,
    'hex': hex,
    'map': map,
    'range': range,
    'str': str,
    "int": int,
    "float": float,
    "dict": dict,
    "set": set,
    "sorted":sorted,
    "json":json,
    'zip': zip,
    'list': list,
    'bool': bool,
    "sin": math.sin,
    "pi": math.pi,
    "math": math,
    "ord": ord,
    "chr": chr,
    "random": random,
    "datetime": datetime.datetime,
    "date": datetime.date,
    "time": datetime.time,
    "timedelta": datetime.timedelta,
    "timestamp": datetime.datetime.fromtimestamp,
    "message": None,
    "re": re,

}

localenv = {}



def attrpath(node):
    if isinstance(node, ast.Attribute):
        first, rest = attrpath(node.value)
        return first, rest + [node.attr]
    else:
        return node.id, []


def eval_(expr, env):
    body = ast.parse(expr, mode='single').body
    for stmt_or_expr in body:
        response = None
        if isinstance(stmt_or_expr, ast.Expr):
            response = eval_expr(stmt_or_expr.value, env)
            #response = timed(eval_expr, args=(stmt_or_expr.value, env))
        elif isinstance(stmt_or_expr, ast.Assign):
            env = eval_assign(stmt_or_expr, env)
        else:
            raise Exception(ast.dump(stmt_or_expr))

        if response is not None:
            yield response


def eval_assign(node, env):
    val = timed(eval_expr, args=(node.value, env))
    for x in node.targets:
        if isinstance(x, ast.Attribute):
            first, rest = attrpath(x)
            setattr(timed(eval_expr, args=(x.value, localenv)), x.attr, val)
        elif isinstance(x, ast.Name):
            if x.id in globalenv:
                env[x.id] = val
            else:
                localenv[x.id] = val
                env[x.id] = val
        elif isinstance(x, ast.Subscript):
            raise Exception(ast.dump(x))
        else:
            raise Exception(ast.dump(x))
    return env


def eval_expr(node, env):
    if node is not None:
        if type(node) in exprs:
            return exprs[type(node)](**ChainMap({"env": env}, dict(ast.iter_fields(node))))
        else:
            try:
                raise Exception(ast.dump(node))
            except TypeError:
                raise Exception(node)
    else:
        return None


def lambda_(args, body, env):
    fields = dict(ast.iter_fields(args))
    fields['defaults'] = [eval_expr(default, env) for default in args.defaults]
    if "kwonlyargs" in fields:
        fields["kw_defaults"] = [eval_expr(kw_default, env) if
                                 kw_default is not None else None
                                 for kw_default in args.kw_defaults]
        fields["kw_defaults_"] = args.kw_defaults
    return Lambda(body, env, fields)


class Lambda():
    def __init__(self, body, env, fields):
        self.body = body
        self.env = env
        self.fields = fields

    def __call__(self, *args, **kwargs):
        env = self.env.copy()
        env.update(globalenv)
        env.update(localenv)
        return eval_expr(self.body, getenv(funcname="<lambda>", call_args=args, call_kwargs=kwargs,
                                           env=env, **self.fields))

    def __repr__(self):
        return "lambda " + ",".join([x.arg for y in self.fields.values() if y for x in y]) + ": " + ast_to_string(
            self.body)


def compare_(left, ops, comparators, env):
    left = eval_expr(left, env)
    comparators = [eval_expr(comparator, env) for comparator in comparators]
    comparisons = zip([left] + comparators, ops, comparators)
    return all(compares[type(op)](left, right) for left, op, right in comparisons)


def call_(func, args, starargs, keywords, kwargs, env):
    args2 = [eval_expr(arg, env) for arg in args]
    if starargs:
        args2.extend(eval_expr(starargs, env))
    kwargs2 = {keyword.arg: eval_expr(keyword.value, env) for keyword in keywords}
    if kwargs:
        kwargs2.update(eval_expr(kwargs, env))
    return eval_expr(func, env)(*args2, **kwargs2)


def bind_name(id, ctx, rhs, env):
    env[id] = rhs


def bind_iter(elts, ctx, rhs, env):
    for elt, subrhs in zip(elts, rhs):
        bind(elt, subrhs, env)


def bind_arg(arg, annotation, rhs, env):
    env[arg] = rhs


binds = {
    ast.Name: bind_name,
    ast.List: bind_iter,
    ast.Tuple: bind_iter,
    ast.arg: bind_arg,
}


def bind(node, rhs, env):
    binds[type(node)](rhs=rhs, env=env, **dict(ast.iter_fields(node)))
    return env


def raise_(string):
    raise Exception(string)


def generate(gens, env):
    if not gens:
        yield env
    else:
        gen = gens[0]
        for it in eval_expr(gen.iter, env):
            for genenv in generate(gens[1:], bind(gen.target, it, env.copy())):
                if all(eval_expr(if_, genenv) for if_ in gen.ifs):
                    yield genenv


def getenv(funcname, args, vararg, kwarg, defaults, call_args, call_kwargs, env,
           kwonlyargs=None, kw_defaults=None, kw_defaults_=None):
    subenv = OrderedDict()

    for param, arg in zip(args, call_args):
        bind(param, arg, subenv)
    varargs = call_args[len(args):]
    if vararg:
        subenv[vararg.arg] = varargs
    elif varargs:
        raise TypeError("%s() takes %s positional arguments but %s %s given" %
                        (funcname, len(args), len(call_args), "was" if len(call_args) == 1 else "were"))
    kwonlyargs_ = []
    kwenv = OrderedDict()
    if kwonlyargs:
        for param in kwonlyargs:
            bind(param, None, kwenv)
            kwonlyargs_.append(param.arg)
    for param in args:
        bind(param, None, kwenv)

    kwargsd = []
    for key, value in call_kwargs.items():
        if key in subenv:
            raise TypeError("%s() got multiple values for argument '%s'" % key)
        elif key in kwenv:
            subenv[key] = value
        elif key in args:
            subenv[key] = value
        else:
            kwargsd.append(key)
    if kwarg:
        subenv[kwarg.arg] = kwargsd
    elif kwargsd:
        raise TypeError("%s() got an unexpected keyword argument '%s'" % (funcname, kwargsd[0]))

    newenv = OrderedDict()
    if not kwonlyargs:
        for param, default in zip(args[::-1], defaults[::-1]):
            bind(param, default, newenv)
    else:
        for param, default in [(p, d) for p, ds, d in zip(kwonlyargs, kw_defaults_, kw_defaults) if ds]:
            bind(param, default, newenv)
    newenv.update(subenv)
    kwmissing = []
    posmissing = []
    for key in kwenv.keys():
        if key not in newenv:
            if key in kwonlyargs_:
                kwmissing.append(key)
            else:
                posmissing.append(key)
    if posmissing:
        raise TypeError("%s() missing %s required positional argument" % (funcname, len(posmissing)) + "%s: %s" %
                        ("s" if len(posmissing) > 1 else "",
                         "'%s'" % posmissing[0] +
                         ((", " + ", ".join(["'%s'" % x for x in posmissing[1:-1]])) if len(posmissing) > 2 else "") +
                         (" and '%s'" % posmissing[-1] if len(posmissing) > 1 else "")))
    if kwmissing:
        raise TypeError("%s() missing %s required keyword-only argument" % (funcname, len(kwmissing)) + "%s: %s" %
                        ("s" if len(kwmissing) > 1 else "",
                         "'%s'" % kwmissing[0] +
                         ((", " + ", ".join(["'%s'" % x for x in kwmissing[1:-1]])) if len(kwmissing) > 2 else "") +
                         (" and '%s'" % kwmissing[-1] if len(kwmissing) > 1 else "")))
    for key, value in env.items():
        if key not in newenv:
            newenv[key] = value
    return newenv


@plugin
class Eval:
    # #@on_load
    # def init(self):
    #     con = pymongo.MongoClient()
    #     db = con["seval"]
    #     for table in db.collection_names():
    #         for record in db[table].find({"bin": {"$exists": True}}):
    #             userenv[table][record["key"]] = pickle.loads(record["bin"])
    #
    # #@on_unload
    # def save(self):
    #     con = pymongo.MongoClient()
    #     db = con["seval"]
    #     for user, space in userenv.items():
    #         for key, val in space.items():
    #             db[user].insert({"key": key, "bin": pickle.dumps(val)})

    @command(">", bufferreplace=False, argparse=False)
    @command("seval", bufferreplace=False, argeparse=False)
    def calc(self, arg, target):
        """oh boy, so this is a python interpreter, you can do most things you could do from a terminal, but only single line statements are allowed. you can chain multiple single statements together using ';' and you can access any piped in message via 'message'"""
        env = dict(globalenv)
        env.update(localenv)

        try:
            while 1:
                message = yield
                if message is None:
                    env["message"] = arg
                    for response in eval_(arg.text.strip(), env):
                        target.send(arg.reply(response, repr(response)))
                else:
                    env["message"] = message
                    for response in eval_(arg.text.strip(), env):
                        target.send(arg.reply(response, repr(response)))

        except GeneratorExit:
            target.close()

    @command("filter", bufferreplace=False, argeparse=False)
    def filt(self, arg, target):
        env = dict(globalenv)
        env.update(localenv)
        try:
            while 1:
                message = yield
                if message is None:
                    pass
                else:
                    env["message"] = message
                    response = False
                    for response in eval_(arg.text.strip(), env):
                        pass

                    if response:
                        target.send(message)

        except GeneratorExit:
            target.close()

    @command("liteval", bufferreplace=False, argeparse=False)
    def liteval(self, message):
        'will evaluate python literals. pretty simple version of seval'
        return message.reply(repr(ast.literal_eval(message.text.strip())))
