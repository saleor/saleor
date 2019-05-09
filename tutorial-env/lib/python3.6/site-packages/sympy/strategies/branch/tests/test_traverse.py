from sympy import Basic
from sympy.strategies.branch.traverse import top_down, sall
from sympy.strategies.branch.core import do_one, identity

def inc(x):
    if isinstance(x, int):
        yield x + 1

def test_top_down_easy():
    expr     = Basic(1, 2)
    expected = Basic(2, 3)
    brl = top_down(inc)

    assert set(brl(expr)) == {expected}

def test_top_down_big_tree():
    expr     = Basic(1, Basic(2), Basic(3, Basic(4), 5))
    expected = Basic(2, Basic(3), Basic(4, Basic(5), 6))
    brl = top_down(inc)

    assert set(brl(expr)) == {expected}

def test_top_down_harder_function():
    def split5(x):
        if x == 5:
            yield x - 1
            yield x + 1

    expr     = Basic(Basic(5, 6), 1)
    expected = {Basic(Basic(4, 6), 1), Basic(Basic(6, 6), 1)}
    brl = top_down(split5)

    assert set(brl(expr)) == expected

def test_sall():
    expr     = Basic(1, 2)
    expected = Basic(2, 3)
    brl = sall(inc)

    assert list(brl(expr)) == [expected]

    expr     = Basic(1, 2, Basic(3, 4))
    expected = Basic(2, 3, Basic(3, 4))
    brl = sall(do_one(inc, identity))

    assert list(brl(expr)) == [expected]
