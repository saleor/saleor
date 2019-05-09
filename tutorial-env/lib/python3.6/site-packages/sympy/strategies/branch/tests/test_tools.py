from sympy.strategies.branch.tools import canon
from sympy import Basic


def posdec(x):
    if isinstance(x, int) and x > 0:
        yield x-1
    else:
        yield x

def branch5(x):
    if isinstance(x, int):
        if 0 < x < 5:
            yield x-1
        elif 5 < x < 10:
            yield x+1
        elif x == 5:
            yield x+1
            yield x-1
        else:
            yield x

def test_zero_ints():
    expr = Basic(2, Basic(5, 3), 8)
    expected = {Basic(0, Basic(0, 0), 0)}

    brl = canon(posdec)
    assert set(brl(expr)) == expected

def test_split5():
    expr = Basic(2, Basic(5,  3), 8)
    expected = set([Basic(0, Basic(0,  0), 10),
                 Basic(0, Basic(10, 0), 10)])

    brl = canon(branch5)
    assert set(brl(expr)) == expected
