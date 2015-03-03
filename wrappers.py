import inspect
import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from multiprocessing import TimeoutError

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


def trigger(trigger_=None):
    def wrapper(func):
        if not hasattr(func, '_triggers'):
            func._triggers = []
        func._triggers.append(trigger_)
        return func
    if not trigger:
        raise Exception("no trigger specified")
    else:
        return wrapper


def command(name=None, **kwargs):
    def wrapper(func):
        if not hasattr(func, '_commands'):
            func._commands = []
        func2 = dict(kwargs, command=name if not inspect.isfunction(name) and name is not None else func.__name__)
        func._commands.append(func2)
        return func        
    if inspect.isfunction(name):
        return wrapper(name)
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


def event(event_):
    def wrapper(func):
        if not hasattr(func, '_handlers'):
            func._handlers = []
        func._handlers.append(event_)
        return func
    return wrapper


def timed(func, args=(), kwargs={}, timeout=2, proc=True):
    with (Pool if proc else ThreadPool)(processes=1) as pool:
        result = pool.apply_async(func, args=args, kwds=kwargs)
        try:
            return result.get(timeout)
        except TimeoutError as e:
            pool.terminate()
            raise Exception("Took more than %s seconds" % timeout)


def _plugin__init__(self,bot):
    self.bot = bot
    self._onLoads = []
    self._onUnloads = []
    self._triggers = []
    self._commands = []
    self._regexes = []
    self._handlers = []
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
        if hasattr(func, '_handlers'):
            for event in func._handlers:
                self._handlers.append((event,func))