from sympy.strategies.tools import subs, typed
from sympy.strategies.rl import rm_id
from sympy import Basic

def test_subs():
    from sympy import symbols
    a,b,c,d,e,f = symbols('a,b,c,d,e,f')
    mapping = {a: d, d: a, Basic(e): Basic(f)}
    expr   = Basic(a, Basic(b, c), Basic(d, Basic(e)))
    result = Basic(d, Basic(b, c), Basic(a, Basic(f)))
    assert subs(mapping)(expr) == result

def test_subs_empty():
    assert subs({})(Basic(1, 2)) == Basic(1, 2)

def test_typed():
    class A(Basic):
        pass
    class B(Basic):
        pass
    rmzeros = rm_id(lambda x: x == 0)
    rmones  = rm_id(lambda x: x == 1)
    remove_something = typed({A: rmzeros, B: rmones})

    assert remove_something(A(0, 1)) == A(1)
    assert remove_something(B(0, 1)) == B(0)
