import inspect
import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from multiprocessing import TimeoutError as TE
import os


def plugin(desc=None):
    def wrapper(clas):
        clas._plugin = True
        clas._plugin_desc = desc
        clas._plugin__init__ = _plugin__init__
        return clas
    if inspect.isclass(desc):
        return wrapper(desc)
    else:
        return wrapper

def onLoad(func):
    if not hasattr(func, '_onLoad'):
        func._onLoad = True
    return func


def onUnload(func):
    if not hasattr(func, '_onUnload'):
        func._onUnload = True
    return func


def trigger(trigger=None):
    def wrapper(func):
        if not hasattr(func, '_triggers'):
            func._triggers = []
        func._triggers.append(trigger)
        print(func._triggers)
        return func
    if not trigger:
        raise Exception("no trigger specified")
    else:
        return wrapper


def command(command=None,**kwargs):
    def wrapper(func):
        if not hasattr(func, '_commands'):
            func._commands = []
        func2 = dict(kwargs,command=command if not inspect.isfunction(command) else func.__name__)
        func._commands.append(func2)
        return func        
    if inspect.isfunction(command):
        return wrapper(command)
    else:
        return wrapper


def regex(regex=None):
    def wrapper(func):
        if not hasattr(func, '_regexes'):
            func._regexes = []
        func._regexes.append(re.compile(regex))
        return func
    if not regex:
        raise Exception("no regex specified")
    else:
        return wrapper


def timed(func, args=(), kwargs={}, timeout=2,proc=True):
    with (Pool if proc else ThreadPool)(processes=1) as pool:
        result = pool.apply_async(func,args=args,kwds=kwargs)
        try:
            return result.get(timeout)
        except TE as e:
            pool.terminate()
            raise Exception("Took more than %s seconds" % timeout)


def _plugin__init__(self,bot):
    self.bot = bot
    self._onLoads = []
    self._onUnloads = []
    self._triggers = []
    self._commands = []
    self._regexes = []
    for name,func in inspect.getmembers(self, predicate=inspect.ismethod):
        if hasattr(func, '_onLoad'):
            self._onLoads.append(func)
        if hasattr(func, '_onUnload'):
            self._onUnloads.append(func)
        if hasattr(func, '_triggers'):
            for trigger in func._triggers:
                self._triggers.append((trigger,func))
        if hasattr(func, '_commands'):
            for args in func._commands:
                self._commands.append((func,args))
        if hasattr(func, '_regexes'):
            for regex in func._regexes:
                self._regexes.append((regex,func))