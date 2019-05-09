"""
rename this to test_assumptions.py when the old assumptions system is deleted
"""
from sympy.abc import x, y
from sympy.assumptions.assume import global_assumptions, Predicate
from sympy.assumptions.ask import _extract_facts, Q
from sympy.core import symbols
from sympy.logic.boolalg import Or
from sympy.printing import pretty
from sympy.utilities.pytest import XFAIL


def test_equal():
    """Test for equality"""
    assert Q.positive(x) == Q.positive(x)
    assert Q.positive(x) != ~Q.positive(x)
    assert ~Q.positive(x) == ~Q.positive(x)


def test_pretty():
    assert pretty(Q.positive(x)) == "Q.positive(x)"
    assert pretty(
        set([Q.positive, Q.integer])) == "{Q.integer, Q.positive}"


def test_extract_facts():
    a, b = symbols('a b', cls=Predicate)
    assert _extract_facts(a(x), x) == a
    assert _extract_facts(a(x), y) is None
    assert _extract_facts(~a(x), x) == ~a
    assert _extract_facts(~a(x), y) is None
    assert _extract_facts(a(x) | b(x), x) == a | b
    assert _extract_facts(a(x) | ~b(x), x) == a | ~b
    assert _extract_facts(a(x) & b(y), x) == a
    assert _extract_facts(a(x) & b(y), y) == b
    assert _extract_facts(a(x) | b(y), x) == None
    assert _extract_facts(~(a(x) | b(y)), x) == ~a


def test_global():
    """Test for global assumptions"""
    global_assumptions.add(Q.is_true(x > 0))
    assert Q.is_true(x > 0) in global_assumptions
    global_assumptions.remove(Q.is_true(x > 0))
    assert not Q.is_true(x > 0) in global_assumptions
    # same with multiple of assumptions
    global_assumptions.add(Q.is_true(x > 0), Q.is_true(y > 0))
    assert Q.is_true(x > 0) in global_assumptions
    assert Q.is_true(y > 0) in global_assumptions
    global_assumptions.clear()
    assert not Q.is_true(x > 0) in global_assumptions
    assert not Q.is_true(y > 0) in global_assumptions
