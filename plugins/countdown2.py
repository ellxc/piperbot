from itertools import chain, combinations_with_replacement,permutations
from operator import add,sub,mul,truediv

OPS = {"+": add, "-": sub, "/": truediv, "*": mul}


def solve_countdown(target,numbers):
    number_combinations = chain.from_iterable(permutations(numbers, r) for r in range(len(numbers)+1)[2:])
    for numberset in number_combinations:
        operator_combinations = list(combinations_with_replacement("+-/*", len(numberset)-2))
        for last in "+-*/":
            for opset in operator_combinations:
                first = numberset[:2]
                middle = rpn_permutations(chain(numberset[2:], opset))
                for mid in middle:
                    comb = list(chain(first, mid, last))
                    try:
                        result = calc_rpn(comb)
                    except:
                        continue
                    if result == target:
                        return comb


def rpn_permutations(iterable):
    pool = tuple(iterable)
    n = len(pool)
    r = n
    indices = list(range(n))
    cycles = list(range(n, n-r, -1))
    yield tuple(pool[i] for i in indices[:r])
    while n:
        for i in reversed(range(r)):
            cycles[i] -= 1
            if cycles[i] == 0:
                indices[i:] = indices[i+1:] + indices[i:i+1]
                cycles[i] = n - i
            else:
                j = cycles[i]
                indices[i], indices[-j] = indices[-j], indices[i]
                temp = tuple(pool[i] for i in indices[:r])
                if is_valid_rpn(temp):
                    yield temp
                break
        else:
            return


def is_valid_rpn(iterable):
    opcount = 0
    for i,x in zip(iterable, range(1,len(iterable))):
        if i in OPS:
            opcount += 1
        if opcount > x+1 - opcount:
            return False
    return True

def calc_rpn(inp):
    stack = []
    for token in inp:
        if token in OPS:
            a, b = stack.pop(), stack.pop()
            stack.append(OPS[token](a, b))
        else:
            stack.append(token)

    return stack.pop()

def postfix_to_infix(iterable):
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




if __name__ == "__main__":

    print( postfix_to_infix(solve_countdown(10,[1,2,3,4])) + " = 10")
