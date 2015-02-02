import ast
import math
from collections import OrderedDict, ChainMap


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
    ast.Slice: lambda env, expr, lower, upper, step: expr[eval_expr(lower, env):eval_expr(upper, env):eval_expr(step, env)],
    ast.Index: lambda env, expr, value: expr[eval_expr(value, env)],
}

exprs = {
    ast.BoolOp: lambda env, op, values: boolops[type(op)](eval_expr(value, env) for value in values),
    ast.BinOp: lambda env, op, left, right: binops[type(op)](eval_expr(left, env), eval_expr(right, env)),
    ast.UnaryOp: lambda env, op, operand: unaryops[type(op)](eval_expr(operand, env)),
    ast.Lambda: lambda env, args, body: lambda_(args, body, env),
    ast.IfExp: lambda env, test, body, orelse: eval_expr(body, env) if eval_expr(test, env) else eval_expr(orelse, env),
    ast.Dict: lambda env, keys, values: {eval_expr(key, env): eval_expr(value, env) for key, value in zip(keys, values)},
    ast.Set: lambda env, elts: {eval_expr(elt, env) for elt in elts},
    ast.ListComp: lambda env, elt, generators: [eval_expr(elt, genenv) for genenv in generate(generators, env)],
    ast.SetComp: lambda env, elt, generators: {eval_expr(elt, genenv) for genenv in generate(generators, env)},
    ast.DictComp: lambda env, key, value, generators: {eval_expr(key, genenv): eval_expr(value, genenv) for genenv in
                                                       generate(generators, env)},
    ast.Compare: lambda env, left, ops, comparators: compare_(left, ops, comparators, env),
    ast.Call: lambda env, func, args, starargs, keywords, kwargs: call_(func, args, starargs, keywords, kwargs, env),
    ast.Num: lambda env, n: n,
    ast.Str: lambda env, s: s,
    ast.Subscript: lambda env, ctx, value, slice: slices[type(slice)](env=env, **dict(slice.iter_fields())),
    ast.Name: lambda env, ctx, id: env[id] if id in env else raise_("name '%s' is not defined" % id),
    ast.List: lambda env, ctx, elts: list(eval_expr(elt, env) for elt in elts),
    ast.Tuple: lambda env, ctx, elts: tuple(eval_expr(elt, env) for elt in elts),
    ast.NameConstant: lambda env, value: value,
}


globalenv = {
    'len': len,
    'map': map,
    'range': range,
    'str': str,
    'zip': zip,
    'list': list,
    'bool': bool,
    "sin": math.sin,
    "pi": math.pi
}

userenv = {}


def eval_(expr):
    env = userenv.copy()
    env.update(globalenv)
    for stmt_or_expr in ast.parse(expr, mode='single').body:
        response = None
        if isinstance(stmt_or_expr, ast.Expr):
            response = eval_expr(stmt_or_expr.value, env)
        elif isinstance(stmt_or_expr, ast.Assign):
            env = eval_Assign(stmt_or_expr, env)

        if response is not None:
            yield response


def eval_Assign(node, env):
    try:
        val = eval_expr(node.value, env)
        for x in node.targets:
            if x.id in globalenv:
                env[x.id] = val
            else:
                userenv[x.id] = val
        return env
    except:
        raise Exception(ast.dump(node))


def eval_expr(node, env):
    if type(node) in exprs:
        return exprs[type(node)](env=env, **dict(ast.iter_fields(node)))
    else:
        try:
            raise Exception(ast.dump(node))
        except TypeError:
            raise Exception(node)


def lambda_(args, body, env):
    fields = dict(ast.iter_fields(args))
    fields['defaults'] = [eval_expr(default, env) for default in args.defaults]
    if "kwonlyargs" in fields:
        fields["kw_defaults"] = [eval_expr(kw_default, env) if kw_default is not None else None for kw_default in args.kw_defaults]
        fields["kw_defaults_"] = args.kw_defaults
    return lambda *args, **kwargs: eval_expr(body, getenv(funcname="<lambda>",call_args=args, call_kwargs=kwargs, env=env, **fields))


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
           kwonlyargs=[], kw_defaults=[], kw_defaults_=[]):

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
                         ((", " +", ".join(["'%s'" % x for x in posmissing[1:-1]])) if len(posmissing) > 2 else "") +
                         (" and '%s'" % posmissing[-1] if len(posmissing) > 1 else "")))
    if kwmissing:
        raise TypeError("%s() missing %s required keyword-only argument" % (funcname, len(kwmissing)) + "%s: %s" %
                        ("s" if len(kwmissing) > 1 else "",
                         "'%s'" % kwmissing[0] +
                         ((", " +", ".join(["'%s'" % x for x in kwmissing[1:-1]])) if len(kwmissing) > 2 else "") +
                         (" and '%s'" % kwmissing[-1] if len(kwmissing) > 1 else "")))
    for key, value in env.items():
        if key not in newenv:
            newenv[key] = value
    return newenv

from plugins.stuff.BasePlugin import *

@plugin
class eval:
    @command("calc")
    @command(">")
    def calc(self, message):
        for response in eval_(message.text.strip()):
            yield message.reply(repr(response))

    @command("liteval")
    def liteval(selfself, message):
        yield message.reply(repr(ast.literal_eval(message.text.strip())))