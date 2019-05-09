from sympy import Add, Basic, symbols, Symbol
from sympy.unify.core import Compound, Variable
from sympy.unify.usympy import (deconstruct, construct, unify, is_associative,
        is_commutative)
from sympy.abc import x, y, z, n
from sympy.utilities.pytest import XFAIL

def test_deconstruct():
    expr     = Basic(1, 2, 3)
    expected = Compound(Basic, (1, 2, 3))
    assert deconstruct(expr) == expected

    assert deconstruct(1) == 1
    assert deconstruct(x) == x
    assert deconstruct(x, variables=(x,)) == Variable(x)
    assert deconstruct(Add(1, x, evaluate=False)) == Compound(Add, (1, x))
    assert deconstruct(Add(1, x, evaluate=False), variables=(x,)) == \
              Compound(Add, (1, Variable(x)))

def test_construct():
    expr     = Compound(Basic, (1, 2, 3))
    expected = Basic(1, 2, 3)
    assert construct(expr) == expected

def test_nested():
    expr = Basic(1, Basic(2), 3)
    cmpd = Compound(Basic, (1, Compound(Basic, (2,)), 3))
    assert deconstruct(expr) == cmpd
    assert construct(cmpd) == expr

def test_unify():
    expr = Basic(1, 2, 3)
    a, b, c = map(Symbol, 'abc')
    pattern = Basic(a, b, c)
    assert list(unify(expr, pattern, {}, (a, b, c))) == [{a: 1, b: 2, c: 3}]
    assert list(unify(expr, pattern, variables=(a, b, c))) == \
            [{a: 1, b: 2, c: 3}]

def test_unify_variables():
    assert list(unify(Basic(1, 2), Basic(1, x), {}, variables=(x,))) == [{x: 2}]

def test_s_input():
    expr = Basic(1, 2)
    a, b = map(Symbol, 'ab')
    pattern = Basic(a, b)
    assert list(unify(expr, pattern, {}, (a, b))) == [{a: 1, b: 2}]
    assert list(unify(expr, pattern, {a: 5}, (a, b))) == []

def iterdicteq(a, b):
    a = tuple(a)
    b = tuple(b)
    return len(a) == len(b) and all(x in b for x in a)

def test_unify_commutative():
    expr = Add(1, 2, 3, evaluate=False)
    a, b, c = map(Symbol, 'abc')
    pattern = Add(a, b, c, evaluate=False)

    result  = tuple(unify(expr, pattern, {}, (a, b, c)))
    expected = ({a: 1, b: 2, c: 3},
                {a: 1, b: 3, c: 2},
                {a: 2, b: 1, c: 3},
                {a: 2, b: 3, c: 1},
                {a: 3, b: 1, c: 2},
                {a: 3, b: 2, c: 1})

    assert iterdicteq(result, expected)

def test_unify_iter():
    expr = Add(1, 2, 3, evaluate=False)
    a, b, c = map(Symbol, 'abc')
    pattern = Add(a, c, evaluate=False)
    assert is_associative(deconstruct(pattern))
    assert is_commutative(deconstruct(pattern))

    result   = list(unify(expr, pattern, {}, (a, c)))
    expected = [{a: 1, c: Add(2, 3, evaluate=False)},
                {a: 1, c: Add(3, 2, evaluate=False)},
                {a: 2, c: Add(1, 3, evaluate=False)},
                {a: 2, c: Add(3, 1, evaluate=False)},
                {a: 3, c: Add(1, 2, evaluate=False)},
                {a: 3, c: Add(2, 1, evaluate=False)},
                {a: Add(1, 2, evaluate=False), c: 3},
                {a: Add(2, 1, evaluate=False), c: 3},
                {a: Add(1, 3, evaluate=False), c: 2},
                {a: Add(3, 1, evaluate=False), c: 2},
                {a: Add(2, 3, evaluate=False), c: 1},
                {a: Add(3, 2, evaluate=False), c: 1}]

    assert iterdicteq(result, expected)

def test_hard_match():
    from sympy import sin, cos
    expr = sin(x) + cos(x)**2
    p, q = map(Symbol, 'pq')
    pattern = sin(p) + cos(p)**2
    assert list(unify(expr, pattern, {}, (p, q))) == [{p: x}]

def test_matrix():
    from sympy import MatrixSymbol
    X = MatrixSymbol('X', n, n)
    Y = MatrixSymbol('Y', 2, 2)
    Z = MatrixSymbol('Z', 2, 3)
    assert list(unify(X, Y, {}, variables=[n, Symbol('X')])) == [{Symbol('X'): Symbol('Y'), n: 2}]
    assert list(unify(X, Z, {}, variables=[n, Symbol('X')])) == []

def test_non_frankenAdds():
    # the is_commutative property used to fail because of Basic.__new__
    # This caused is_commutative and str calls to fail
    expr = x+y*2
    rebuilt = construct(deconstruct(expr))
    # Ensure that we can run these commands without causing an error
    str(rebuilt)
    rebuilt.is_commutative

def test_FiniteSet_commutivity():
    from sympy import FiniteSet
    a, b, c, x, y = symbols('a,b,c,x,y')
    s = FiniteSet(a, b, c)
    t = FiniteSet(x, y)
    variables = (x, y)
    assert {x: FiniteSet(a, c), y: b} in tuple(unify(s, t, variables=variables))

def test_FiniteSet_complex():
    from sympy import FiniteSet
    a, b, c, x, y, z = symbols('a,b,c,x,y,z')
    expr = FiniteSet(Basic(1, x), y, Basic(x, z))
    pattern = FiniteSet(a, Basic(x, b))
    variables = a, b
    expected = tuple([{b: 1, a: FiniteSet(y, Basic(x, z))},
                      {b: z, a: FiniteSet(y, Basic(1, x))}])
    assert iterdicteq(unify(expr, pattern, variables=variables), expected)

@XFAIL
def test_and():
    variables = x, y
    str(list(unify((x>0) & (z<3), pattern, variables=variables)))

def test_Union():
    from sympy import Interval
    assert list(unify(Interval(0, 1) + Interval(10, 11),
                      Interval(0, 1) + Interval(12, 13),
                      variables=(Interval(12, 13),)))

def test_is_commutative():
    assert is_commutative(deconstruct(x+y))
    assert is_commutative(deconstruct(x*y))
    assert not is_commutative(deconstruct(x**y))

def test_commutative_in_commutative():
    from sympy.abc import a,b,c,d
    from sympy import sin, cos
    eq = sin(3)*sin(4)*sin(5) + 4*cos(3)*cos(4)
    pat = a*cos(b)*cos(c) + d*sin(b)*sin(c)
    assert next(unify(eq, pat, variables=(a,b,c,d)))
