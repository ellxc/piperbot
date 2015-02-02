from functools import cmp_to_key

def subtract(x, y):
    return x-y


def add(x, y):
    if x <= y:
        return x+y
    raise ValueError


def multiply(x, y):
    if x <= y or x == 1 or y == 1:
        return x*y
    raise ValueError


def divide(x, y):
    if not y or x % y or y == 1:
        raise ValueError
    return x/y

add.str = '+'
multiply.str = '*'
subtract.str = '-'
divide.str = '/'

OPS = [add, subtract, multiply, divide]


def rpn_generator(numbers, depth=0):
    """Generates all permuations of RPN expression for given numbers"""
    for i in range(len(numbers)):
        yield ([numbers[i]], numbers[:i]+numbers[i+1:], numbers[i])
    if len(numbers) >= 2+depth:
        for rhs, rrs, rv in rpn_generator(numbers, depth+1):
            for lhs, lrs, lv in rpn_generator(rrs, depth):
                for op in OPS:
                    try:
                        yield ([lhs, rhs, op], lrs, op(lv, rv))
                    except ValueError:
                        pass


def find_first_match(target, numbers):
    """Find the first matching expression"""
    for expression, s, value in rpn_generator(numbers):
        if value == target:
            return expression
    return []


def find_first_or_closest(target, numbers):
    """Find the first matching expression or the closest"""
    gen = rpn_generator(numbers)
    expression1, s, value1 = gen.__next__()
    if value1 == target:
        return expression1, target

    closest_v = value1
    closest_e = expression1

    for expression, s, value in rpn_generator(numbers):
        if value == target:
            return expression, target
        elif abs(target - value) < abs(target - closest_v):
            closest_v = value
            closest_e = expression
    return closest_e, closest_v



def find_all_matches(target, numbers):
    """Generates all matching expressions"""
    for expression, s, value in rpn_generator(numbers):
        if value == target:
            yield expression

def find_all_or_closest(target, numbers):
    """Find the first matching expression or the closest"""
    gen = rpn_generator(numbers)
    expression1, s, value1 = gen.__next__()
    found = False
    if value1 == target:
        yield expression1, target
        found = True

    closest_v = value1
    closest_e = expression1

    for expression, s, value in rpn_generator(numbers):
        if value == target:
            yield expression, target
            found = True
        elif abs(target - value) < abs(target - closest_v):
            closest_v = value
            closest_e = expression
    if not found:
        yield closest_e, closest_v


def flatten_expression(e):
    """flattens a raw expression to a single array"""
    if len(e)==3:
        for y in flatten_expression(e[0]):
            yield y
        for x in flatten_expression(e[1]):
            yield x
        yield e[2].str
    elif len(e)==1:
        yield e[0]

def postfix_to_infix(iterable):
    """Converts RPN to human readable infix"""

    class Intermediate():
        def __init__(self, expr, priority=False):
            self.expr = expr
            self.priority = priority

    stack = []
    for token in iterable:
        if token == "+" or token == "-":
            right = stack.pop()
            left = stack.pop()
            temp = Intermediate(left.expr + token + right.expr, True)
            stack.append(temp)
        elif token == "*" or token == "/":
            right = stack.pop()
            if right.priority:
                right = Intermediate("(" + right.expr + ")")
            left = stack.pop()
            if left.priority:
                left = Intermediate("(" + left.expr + ")")
            temp = Intermediate(left.expr + token + right.expr)
            stack.append(temp)
        else:
            stack.append(Intermediate(str(token)))
    return stack.pop().expr


def solve(target, numbers):
    e, v = find_first_or_closest(target, numbers)
    s = postfix_to_infix(flatten_expression(e))
    return s, v

def solve_best(target,numbers):
    solutions = find_all_or_closest(target, numbers)
    if not solutions:
        return
    firste, firstv = solutions.__next__()
    if firstv != target:
        return postfix_to_infix(flatten_expression(firste)),firstv
    else:
        solutions = list(map(lambda x: (list(flatten_expression(x[0])), x[1]) ,  [(firste, firstv)] + list(solutions)))
        solutions.sort(key=cmp_to_key(lambda x, y: len(x[0])-len(y[0])))
        return postfix_to_infix(solutions[0][0]),target


if __name__=='__main__':
    import time

    def demo(target, numbers):
        print("Looking for:", target)
        print("Given numbers:", numbers)

        start = time.time()
        s, v = solve_best(target, numbers)

        if v ==target:
            print("Found solution:", s, "=", v)
        else:
            print("Found closest:", s, "=", v)
        print("Took", time.time()-start, "seconds.")
        print()

    #demo(234,[100,9,7,6,3,1])
    #demo(923,[7,8,50,8,1,3])
    #demo(638,[7,3,4,5,25,100])
    #demo(600,[50,25,6,7,8,9])
    #demo(15,[6,7,8,10,5,2,2])

    for e,s,v in rpn_generator([2,2]):
        print(list(flatten_expression(e)),v)
