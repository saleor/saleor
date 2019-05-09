from sympy.core.symbol import symbols
from sympy.printing.ccode import ccode
from sympy.codegen.ast import Declaration, Variable, float64, int64
from sympy.codegen.cnodes import (
    alignof, CommaOperator, goto, Label, PreDecrement, PostDecrement, PreIncrement, PostIncrement,
    sizeof, union, struct
)

x, y = symbols('x y')


def test_alignof():
    ax = alignof(x)
    assert ccode(ax) == 'alignof(x)'
    assert ax.func(*ax.args) == ax


def test_CommaOperator():
    expr = CommaOperator(PreIncrement(x), 2*x)
    assert ccode(expr) == '(++(x), 2*x)'
    assert expr.func(*expr.args) == expr


def test_goto_Label():
    s = 'early_exit'
    g = goto(s)
    assert g.func(*g.args) == g
    assert g != goto('foobar')
    assert ccode(g) == 'goto early_exit'

    l = Label(s)
    assert l.is_Atom
    assert ccode(l) == 'early_exit:'
    assert g.label == l
    assert l == Label(s)
    assert l != Label('foobar')


def test_PreDecrement():
    p = PreDecrement(x)
    assert p.func(*p.args) == p
    assert ccode(p) == '--(x)'


def test_PostDecrement():
    p = PostDecrement(x)
    assert p.func(*p.args) == p
    assert ccode(p) == '(x)--'


def test_PreIncrement():
    p = PreIncrement(x)
    assert p.func(*p.args) == p
    assert ccode(p) == '++(x)'


def test_PostIncrement():
    p = PostIncrement(x)
    assert p.func(*p.args) == p
    assert ccode(p) == '(x)++'


def test_sizeof():
    typename = 'unsigned int'
    sz = sizeof(typename)
    assert ccode(sz) == 'sizeof(%s)' % typename
    assert sz.func(*sz.args) == sz
    assert not sz.is_Atom
    assert all(atom == typename for atom in sz.atoms())


def test_struct():
    vx, vy = Variable(x, type=float64), Variable(y, type=float64)
    s = struct('vec2', [vx, vy])
    assert s.func(*s.args) == s
    assert s == struct('vec2', (vx, vy))
    assert s != struct('vec2', (vy, vx))
    assert str(s.name) == 'vec2'
    assert len(s.declarations) == 2
    assert all(isinstance(arg, Declaration) for arg in s.declarations)
    assert ccode(s) == (
        "struct vec2 {\n"
        "   double x;\n"
        "   double y;\n"
        "}")


def test_union():
    vx, vy = Variable(x, type=float64), Variable(y, type=int64)
    u = union('dualuse', [vx, vy])
    assert u.func(*u.args) == u
    assert u == union('dualuse', (vx, vy))
    assert str(u.name) == 'dualuse'
    assert len(u.declarations) == 2
    assert all(isinstance(arg, Declaration) for arg in u.declarations)
    assert ccode(u) == (
        "union dualuse {\n"
        "   double x;\n"
        "   int64_t y;\n"
        "}")
