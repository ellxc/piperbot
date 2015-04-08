import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from multiprocessing import TimeoutError
import functools
import inspect
import string
from enum import IntEnum
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


def adv_command(name=None, **kwargs):
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


        @functools.wraps(func)
        def generator(self, args, target):
            x = func(self, args, target)
            next(x)
            return x

        return generator

    if inspect.isfunction(name):
        return _coroutine(name)
    else:
        return _coroutine


def command(name=None, **kwargs):
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


        @functools.wraps(func)
        def generator(self, args, target):
            def inner(target):
                arg = args
                formats = len(list(string.Formatter().parse(arg.data)))
                try:
                    while True:
                        line = yield
                        if line is None:
                            if formats:
                                x = func(self, arg.reply(arg.data.format(*([""] * formats)), args=arg.args))
                            else:
                                x = func(self, arg)
                        else:
                            if formats:
                                if line.data is not None:
                                    x = func(self, line.reply(arg.data.format(*([line.data] * formats)), args=arg.args))
                                else:
                                    x = func(self, line.reply(arg.data.format(*([""] * formats)), args=arg.args))
                            else:
                                x = func(self, line.reply(line.data, args=arg.args))
                        if x is not None:
                            if inspect.isgenerator(x):
                                for y in x:
                                    target.send(y)
                            else:
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

class extensiontype(IntEnum):
    command = 1
    trigger = 2
    event = 3
    regex = 4

def extension(priority=1, simple=False, type=1, **kwargs):
    def _coroutine(func):

        if hasattr(func, "_extensions"):
            func._extensions.append((priority, type))
            return func

        func._extensions = []
        func._extensions.append((priority, type))

        if inspect.isgeneratorfunction(func) and not simple:
            @functools.wraps(func)
            def generator(self, original, target):
                x = func(self, original, target)
                next(x)
                return x

            return generator
        else:
            @functools.wraps(func)
            def generator(self, original, target):
                def inner(target):
                    try:
                        while True:
                            line = yield
                            if line is not None:
                                x = func(self, line)
                                if inspect.isgenerator(x):
                                    for y in x:
                                        target.send(y)
                                else:
                                    target.send(x)
                    except GeneratorExit:
                        target.close()

                ret = inner(target)
                next(ret)
                return ret

            return generator

    return _coroutine



def arg(arg=None, default=False):
    def wrapper(func):
        if not hasattr(func, '_args'):
            func._args = {}
        func._args[arg] = default
        return func
    if inspect.isfunction(arg):
        raise Exception("no arg specified")
    else:
        return wrapper



def regex(regex=None):
    def wrapper(func):
        if hasattr(func, '_regexes'):
            func._regexes.append(re.compile(regex))
            return func
        func._regexes = []
        func._regexes.append(re.compile(regex))

        @functools.wraps(func)
        def generator(self, target):
            message = yield
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
        def generator(self, target):
            message = yield
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
        def generator(self, target):
            message = yield
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
    self._command_extensions = []
    self._event_extensions = []
    self._trigger_extensions = []
    self._regex_extensions = []
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
        if hasattr(func, '_extensions'):
            for priority, type in func._extensions:
                if type == extensiontype.command:
                    self._command_extensions.append((priority, func))
                elif type == extensiontype.regex:
                    self._regex_extensions.append((priority, func))
                elif type == extensiontype.trigger:
                    self._trigger_extensions.append((priority, func))
                elif type == extensiontype.event:
                    self._event_extensions.append((priority, func))