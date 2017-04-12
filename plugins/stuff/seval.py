import ast
from collections import OrderedDict, ChainMap
import traceback
import sys
import itertools

def and_(args):
    for x in iter(args):
        if not x:
            return x
    return x

boolops = {
    ast.And: and_,  # this functions well enough, who uses 'and' to get values anyway?
    ast.Or: lambda vals: next(itertools.chain(filter(bool, vals),[False])),
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
    ast.Raise: lambda exc, cause, env: Raise_(eval_expr(exc, env)),
    ast.BoolOp: lambda env, op, values: boolops[type(op)](eval_expr(value, env) for value in values),
    ast.BinOp: lambda env, op, left, right: binops[type(op)](eval_expr(left, env), eval_expr(right, env)),
    ast.UnaryOp: lambda env, op, operand: unaryops[type(op)](eval_expr(operand, env)),
    ast.Lambda: lambda env, args, body: Lambda(body, dict(ast.iter_fields(args))),
    ast.IfExp: lambda env, test, body, orelse: eval_expr(body, env) if eval_expr(test, env) else eval_expr(orelse, env),
    ast.Dict: lambda env, keys, values: {eval_expr(key, env):
                                         eval_expr(value, env) for key, value in zip(keys, values)},
    ast.Set: lambda env, elts: {eval_expr(elt, env) for elt in elts},
    ast.ListComp: lambda env, elt, generators: [eval_expr(elt, genenv) for genenv in generate(generators, env)],
    ast.SetComp: lambda env, elt, generators: {eval_expr(elt, genenv) for genenv in generate(generators, env)},
    ast.DictComp: lambda env, key, value, generators: {eval_expr(key, genenv): eval_expr(value, genenv) for genenv in
                                                       generate(generators, env)},
    ast.GeneratorExp: lambda env, elt, generators: (eval_expr(elt, genenv) for genenv in generate(generators, env)),
    ast.Compare: lambda env, left, ops, comparators: compare_(left, ops, comparators, env),
    ast.Call: lambda env, func, args, keywords: call_(func, args, keywords, env),    
    ast.Num: lambda env, n: n,
    ast.Str: lambda env, s: s,
    ast.Bytes: lambda env, s: s,
    ast.Subscript: lambda env, ctx, value, slice: slices[type(slice)](value_=value, env=env, **dict(ast.iter_fields(slice))),
    ast.Name: lambda env, ctx, id: env[id],
    ast.List: lambda env, ctx, elts: list(eval_expr(elt, env) for elt in elts),
    ast.Tuple: lambda env, ctx, elts: tuple(eval_expr(elt, env) for elt in elts),
    ast.NameConstant: lambda env, value: value,
    ast.Attribute: lambda env, value, attr, ctx:
    (getattr(eval_expr(value, env), attr) if isinstance(value, ast.Attribute) else getattr(eval_expr(value, env), attr))
    if not attr.startswith("_") else raise_("access to private fields is disallowed"),
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
    ast.Slice: lambda expr, lower, upper, step, value_=None:
    str(expr) + "[" + ast_to_string(lower) +
    ((":" + ast_to_string(upper) + ((":" + ast_to_string(step)) if step != 1 else "")) if upper else "")
    + "]",
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
    ast.ListComp: lambda elt, generators: "[list comp]",  # raise_([ast.dump(gen) for gen in generators]),
    # "[" + ",".join([eval_expr(elt, genenv) for genenv in generate(generators)]) +"]",
    ast.SetComp: lambda elt, generators: "{set comp}",
    # {eval_expr(elt, genenv) for genenv in generate(generators, env)},
    ast.DictComp: lambda key, value, generators: "{dict comp}",
    ast.GeneratorExp: lambda elt, generators: "(gen exp)",
    # {eval_expr(key, genenv): eval_expr(value, genenv) for genenv in generate(generators, env)},
    ast.Compare: lambda left, ops, comparators: ast_to_string(left) + "".join(
        [str_compares[type(op)] + ast_to_string(compar) for op, compar in zip(ops, comparators)]),
    ast.Call: lambda func, args, starargs, keywords, kwargs:
    ast_to_string(func) + "(" + ", ".join(
        (list(map(ast_to_string, args)) if args else []) + (list(map(ast_to_string, starargs)) if starargs else []) + [
            a + "=" + ast_to_string(b) for a, b in [(keyword.arg, keyword.value) for keyword in keywords]]) + ")",
    # + kwargs]),
    ast.Num: lambda n: str(n),
    ast.Str: lambda s: "'" + s + "'",
    ast.Bytes: lambda s: "b'"+ s + "'",
    ast.Subscript: lambda ctx, value, slice:
    str_slices[type(slice)](value_=value, **dict(ast.iter_fields(slice))),
    ast.Name: lambda ctx, id: id,
    ast.List: lambda ctx, elts: "[" + ", ".join(map(ast_to_string, elts)) + "]",
    ast.Tuple: lambda ctx, elts: "(" + ", ".join([ast_to_string(elt) for elt in elts]) + ")",
    ast.NameConstant: lambda value: str(value),
    ast.Attribute: lambda value, attr, ctx: ast_to_string(value) + "." + attr,
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


def seval(expr, env):
    body = ast.parse(expr, mode='single').body
    responses = []
    try:
        for stmt_or_expr in body:
            response = None
            if isinstance(stmt_or_expr, ast.Expr):
                response = eval_expr(stmt_or_expr.value, env)
            elif isinstance(stmt_or_expr, ast.Assign):
                eval_assign(stmt_or_expr, env)
            elif isinstance(stmt_or_expr, ast.AugAssign):
                augassign(stmt_or_expr, env)
            elif isinstance(stmt_or_expr, ast.Delete):
                eval_del(stmt_or_expr, env)
            else:
                raise Exception(ast.dump(stmt_or_expr))

            if response is not None:
                responses.append(response)
        return responses, env
    except Exception as e:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("*** print_tb:")
        traceback.print_tb(exc_traceback, file=sys.stdout)

        return e, env

def augassign(node, env):
    val_ = ast.BinOp(left=node.target, op=node.op, right=node.value)
    node = ast.Assign(targets=[node.target], value=val_)
    return eval_assign(node, env)

def eval_assign(node, env):
    val = eval_expr(node.value, env)
    for x in node.targets:
        if isinstance(x, ast.Attribute):
            if x.attr.startswith("_"):
                raise Exception("access to private fields is disallowed")
            setattr(eval_expr(x.value, env), x.attr, val)
        elif isinstance(x, ast.Name):
            env[x.id] = val
        elif isinstance(x, ast.Subscript):
            if isinstance(x.slice, ast.Index):
                eval_expr(x.value, env)[eval_expr(x.slice.value, env)] = val
            elif isinstance(x.slice, ast.Slice):
                eval_expr(x.value, env)[slice(eval_expr(x.slice.lower, env), eval_expr(x.slice.upper, env), eval_expr(x.slice.step, env))] = val
        else:
            bind(x, val, env)
    return env

def eval_del(node, env):
    for x in node.targets:
        if isinstance(x, ast.Attribute):
            if x.attr.startswith("_"):
                raise Exception("access to private fields is disallowed")
            delattr(eval_expr(x.value, env), x.attr)
        elif isinstance(x, ast.Name):
            env.pop(x.id)
        elif isinstance(x, ast.Subscript):
            if isinstance(x.slice, ast.Index):
                del eval_expr(x.value, env)[eval_expr(x.slice.value, env)]
            elif isinstance(x.slice, ast.Slice):
                del eval_expr(x.value, env)[slice(eval_expr(x.slice.lower, env), eval_expr(x.slice.upper, env), eval_expr(x.slice.step, env))]
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

class Lambda():
    def __init__(self, body, fields):
        self.body = body
        self.fields = fields

    def __call__(self, *args, __env__={}, **kwargs):
        return eval_expr(self.body, getenv(funcname="<lambda>", env=__env__, call_args=args, call_kwargs=kwargs, **self.fields))

    def __repr__(self):
        ret = []

        for x in self.fields["args"][slice(0, (-(len(self.fields["defaults"]))) or len(self.fields["args"]))]:
            ret.append(x.arg)
        for x in reversed(["{}={}".format(x.arg, ast_to_string(y)) for x, y in
                           zip(reversed(self.fields["args"]), reversed(self.fields["defaults"]))]):
            ret.append(x)

        if self.fields["vararg"] is not None:
            vararg = "*"+self.fields["vararg"].arg
            ret.append(vararg)


        if self.fields["kwarg"] is not None:
            kwarg = "**"+self.fields["kwarg"].arg
            ret.append(kwarg)

        if self.fields["kwonlyargs"]:
            ret.append("*")
            for p, d in zip(self.fields["kwonlyargs"], self.fields["kw_defaults"]):
                if d is not None:
                    ret.append("{}={}".format(p.arg, ast_to_string(d)))
                else:
                    ret.append(p.arg)

        return "<lambda " + ", ".join(ret) + ": " + ast_to_string(self.body) + ">"


def compare_(left, ops, comparators, env):
    left = eval_expr(left, env)
    comparators = [eval_expr(comparator, env) for comparator in comparators]
    comparisons = zip([left] + comparators, ops, comparators)
    return all(compares[type(op)](left, right) for left, op, right in comparisons)

def call_(func, args, keywords, env):
    args2 = [eval_expr(arg, env) for arg in args]
    kwargs2 = {keyword.arg: eval_expr(keyword.value, env) for keyword in keywords}
    func2 = eval_expr(func, env)
    if isinstance(func2, Lambda):
        return func2(*args2, __env__=env, **kwargs2)
    else:
        return func2(*args2, **kwargs2)


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

def Raise_(exc):
    raise exc

def generate(gens, env):
    if not gens:
        yield env
    else:
        gen = gens[0]
        for it in eval_expr(gen.iter, env):
            for genenv in generate(gens[1:], bind(gen.target, it, env.copy())):
                if all(eval_expr(if_, genenv) for if_ in gen.ifs):
                    yield genenv


def getenv(funcname, args, vararg, kwarg, defaults, call_args, call_kwargs,
           env, kwonlyargs=None, kw_defaults=None):
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

    kwargsd = {}
    for key, value in call_kwargs.items():
        if key in subenv:
            raise TypeError("%s() got multiple values for argument '%s'" % key)
        elif key in kwenv:
            subenv[key] = value
        elif key in args:
            subenv[key] = value
        else:
            kwargsd[key] = value
    if kwarg:
        subenv[kwarg.arg] = kwargsd
    elif kwargsd:
        raise TypeError("%s() got an unexpected keyword argument '%s'" % (funcname, kwargsd.keys()[0]))

    newenv = OrderedDict()
    if not kwonlyargs:
        for param, default in zip(args[::-1], defaults[::-1]):
            bind(param, eval_expr(default, env), newenv)
    else:
        for param, default in [(p, d) for p, d in zip(kwonlyargs, kw_defaults)]:
            if default is not None:
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
