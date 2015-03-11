import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from multiprocessing import TimeoutError
import functools
import inspect
import string

import dill


def plugin(desc=None, thread=False):
    def wrapper(clas):
        clas._plugin = True
        clas._plugin_desc = desc
        clas._plugin__init__ = _plugin__init__
        clas._plugin_thread = thread
        return clas

    if inspect.isclass(desc):
        return wrapper(desc)
    else:
        return wrapper


def on_load(func):
    if not hasattr(func, '_onLoad'):
        func._onLoad = True
    return func


def on_unload(func):
    if not hasattr(func, '_onUnload'):
        func._onUnload = True
    return func


def command(name=None, simple=False, **kwargs):
    def _coroutine(func):

        if hasattr(func, '_commands'):
            func._commands.append(dict(kwargs,
                                       command=name
                                       if not inspect.isfunction(name) and name is not None
                                       else func.__name__))
            return func

        func._commands = []
        func2 = dict(kwargs, command=name if not inspect.isfunction(name) and name is not None else func.__name__)
        func._commands.append(func2)

        if inspect.isgeneratorfunction(func) and not simple:
            @functools.wraps(func)
            def generator(self, args, target):
                x = func(self, args, target)
                next(x)
                return x

            return generator
        else:
            @functools.wraps(func)
            def generator(self, args, target):
                def inner(target):
                    arg = args
                    formats = len(list(string.Formatter().parse(arg.text)))
                    try:
                        while True:
                            line = yield
                            if line is None:
                                x = func(self, arg)
                            else:
                                if formats:
                                    if line.data is not None:
                                        x = func(self, line.reply(text=arg.text.format(*([line.data] * formats))))
                                    else:
                                        x = func(self, line.reply(text=arg.text.format(*([line.text] * formats))))
                                else:
                                    x = func(self, line.reply(text=arg.text + " " + line.text))
                            if x is not None:
                                if inspect.isgenerator(x):
                                    for y in x:
                                        if target is not None:
                                            target.send(y)
                                else:
                                    if target is not None:
                                        target.send(x)
                    except GeneratorExit:
                        if target is not None:
                            target.close()

                ret = inner(target)
                next(ret)
                return ret

            return generator

    if inspect.isfunction(name):
        return _coroutine(name)
    else:
        return _coroutine


def regex(regex=None):
    def wrapper(func):
        if hasattr(func, '_regexes'):
            func._regexes.append(re.compile(regex))
            return func
        func._regexes = []
        func._regexes.append(re.compile(regex))

        @functools.wraps(func)
        def generator(self, message, target):
            x = func(self, message)
            if x is not None:
                if inspect.isgenerator(x):
                    for y in x:
                        target.send(y)
                else:
                    target.send(x)

        return generator

    if regex is None:
        raise Exception("no regex specified")
    else:
        return wrapper


def event(event_):
    def wrapper(func):
        if hasattr(func, '_handlers'):
            func._handlers.append(event_)
            return func
        func._handlers = []
        func._handlers.append(event_)

        @functools.wraps(func)
        def generator(self, message, target):
            x = func(self, message)
            if x is not None:
                if inspect.isgenerator(x):
                    for y in x:
                        target.send(y)
                else:
                    target.send(x)

        return generator

    return wrapper


def trigger(trigger_=None):
    def wrapper(func):
        if hasattr(func, '_triggers'):
            func._triggers.append(trigger_)
            return func
        func._triggers = []
        func._triggers.append(trigger_)

        @functools.wraps(func)
        def generator(self, message, target):
            x = func(self, message)
            if x is not None:
                if inspect.isgenerator(x):
                    for y in x:
                        target.send(y)
                else:
                    target.send(x)

        return generator

    if not trigger:
        raise Exception("no trigger specified")
    else:
        return wrapper


def run_dill_encoded(what):
    fun, args, kwargs = dill.loads(what)
    result = dill.dumps(fun(*args, **kwargs))
    return result


def timed(func, args=(), kwargs={}, timeout=2, proc=True):
    with (Pool if proc else ThreadPool)(processes=1) as pool:
        result = pool.apply_async(run_dill_encoded, (dill.dumps((func, args, kwargs)),))
        try:
            return dill.loads(result.get(timeout))
        except TimeoutError as e:
            pool.terminate()
            raise Exception("Took more than %s seconds" % timeout)


def _plugin__init__(self, bot):
    self.bot = bot
    self._onLoads = []
    self._onUnloads = []
    self._triggers = []
    self._commands = []
    self._regexes = []
    self._handlers = []
    for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
        if hasattr(func, '_onLoad'):
            self._onLoads.append(func)
        if hasattr(func, '_onUnload'):
            self._onUnloads.append(func)
        if hasattr(func, '_triggers'):
            for trigger in func._triggers:
                self._triggers.append((trigger, func))
        if hasattr(func, '_commands'):
            for args in func._commands:
                self._commands.append((func, args))
        if hasattr(func, '_regexes'):
            for regex in func._regexes:
                self._regexes.append((regex, func))
        if hasattr(func, '_handlers'):
            for event in func._handlers:
                self._handlers.append((event, func))