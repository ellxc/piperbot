import inspect
import functools
from queue import Queue

def coroutine(simple=None):
    if isinstance(simple, type(True)):
        simple_ = simple
    elif simple is None:
        simple_ = False
    else:
        simple_ = False


    def _coroutine(func):
        if inspect.isgeneratorfunction(func) and not simple_:
            @functools.wraps(func)
            def generator(*args, **kwargs):
                x = func(*args, **kwargs)
                next(x)
                return x
            return generator
        else:
            @functools.wraps(func)
            def generator(target=None):
                def inner(target):
                    try:
                        while True:
                            line = yield
                            x = func(line)
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

    if inspect.isfunction(simple):
        return _coroutine(simple)
    else:
        return _coroutine


@coroutine
def example(target):    #advanced gen

    # setup


    try:
        while 1:
            x = yield

            def body():

                # body

                yield x[::-1]
            y = body()
            if y is not None:
                if inspect.isgenerator(y):
                    for z in y:
                        target.send(z)
                else:
                    target.send(y)
    except GeneratorExit:

        # teardown


        target.close()

@coroutine
def everyother(target):    #advanced gen
    i = 0
    try:
        while 1:
            x = yield
            def body():
                if i % 2 == 0:
                    return x, i + 1
                return None, i + 1
            y, i = body()
            if y is not None:
                if inspect.isgenerator(y):
                    for z in y:
                        target.send(z)
                else:
                    target.send(y)
    except GeneratorExit:
        target.close()



@coroutine  # simple is assumed if it is not a generator
def caps(line):
    return line.upper()

@coroutine(simple=True)  # simple set manually
def repeattwice(line):
    yield line
    yield line

@coroutine    #  print the end result
def printer(line):
    print("result: ",line)

@coroutine    #  print the end result
def resulter(results):
    try:
        while 1:
            x = yield
            results.put(x)
    except GeneratorExit:
        results.put(None)

def inp(x, pipe):  # input the first data
    pipe.send(x)
    pipe.close()

output = Queue()

pipe = example(repeattwice(everyother(resulter(output))))  # pipe it all together

import _thread

_thread.start_new(inp, ("asd", pipe))
#inp("asd", pipe)  # do the stuff

result = output.get()
while result is not None:
    print(result)
    result =  output.get()


