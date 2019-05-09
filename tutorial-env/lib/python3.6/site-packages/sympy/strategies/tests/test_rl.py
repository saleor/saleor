from sympy.strategies.rl import (rm_id, glom, flatten, unpack, sort, distribute,
        subs, rebuild)
from sympy import Basic

def test_rm_id():
    rmzeros = rm_id(lambda x: x == 0)
    assert rmzeros(Basic(0, 1)) == Basic(1)
    assert rmzeros(Basic(0, 0)) == Basic(0)
    assert rmzeros(Basic(2, 1)) == Basic(2, 1)

def test_glom():
    from sympy import Add
    from sympy.abc import x
    key     = lambda x: x.as_coeff_Mul()[1]
    count   = lambda x: x.as_coeff_Mul()[0]
    newargs = lambda cnt, arg: cnt * arg
    rl = glom(key, count, newargs)

    result   = rl(Add(x, -x, 3*x, 2, 3, evaluate=False))
    expected = Add(3*x, 5)
    assert  set(result.args) == set(expected.args)

def test_flatten():
    assert flatten(Basic(1, 2, Basic(3, 4))) == Basic(1, 2, 3, 4)

def test_unpack():
    assert unpack(Basic(2)) == 2
    assert unpack(Basic(2, 3)) == Basic(2, 3)

def test_sort():
    assert sort(str)(Basic(3,1,2)) == Basic(1,2,3)

def test_distribute():
    class T1(Basic):        pass
    class T2(Basic):        pass

    distribute_t12 = distribute(T1, T2)
    assert distribute_t12(T1(1, 2, T2(3, 4), 5)) == \
            T2(T1(1, 2, 3, 5),
               T1(1, 2, 4, 5))
    assert distribute_t12(T1(1, 2, 3)) == T1(1, 2, 3)

def test_distribute_add_mul():
    from sympy import Add, Mul, symbols
    x, y = symbols('x, y')
    expr = Mul(2, Add(x, y), evaluate=False)
    expected = Add(Mul(2, x), Mul(2, y))
    distribute_mul = distribute(Mul, Add)
    assert distribute_mul(expr) == expected

def test_subs():
    rl = subs(1, 2)
    assert rl(1) == 2
    assert rl(3) == 3

def test_rebuild():
    from sympy import Add
    expr = Basic.__new__(Add, 1, 2)
    assert rebuild(expr) == 3
