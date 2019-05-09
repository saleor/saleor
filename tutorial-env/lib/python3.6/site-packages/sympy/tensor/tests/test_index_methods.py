from sympy.core import symbols, S, Pow, Function
from sympy.functions import exp
from sympy.utilities.pytest import raises
from sympy.tensor.indexed import Idx, IndexedBase
from sympy.tensor.index_methods import IndexConformanceException

from sympy import get_contraction_structure, get_indices


def test_trivial_indices():
    x, y = symbols('x y')
    assert get_indices(x) == (set([]), {})
    assert get_indices(x*y) == (set([]), {})
    assert get_indices(x + y) == (set([]), {})
    assert get_indices(x**y) == (set([]), {})


def test_get_indices_Indexed():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j = Idx('i'), Idx('j')
    assert get_indices(x[i, j]) == (set([i, j]), {})
    assert get_indices(x[j, i]) == (set([j, i]), {})


def test_get_indices_Idx():
    f = Function('f')
    i, j = Idx('i'), Idx('j')
    assert get_indices(f(i)*j) == (set([i, j]), {})
    assert get_indices(f(j, i)) == (set([j, i]), {})
    assert get_indices(f(i)*i) == (set(), {})


def test_get_indices_mul():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j = Idx('i'), Idx('j')
    assert get_indices(x[j]*y[i]) == (set([i, j]), {})
    assert get_indices(x[i]*y[j]) == (set([i, j]), {})


def test_get_indices_exceptions():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j = Idx('i'), Idx('j')
    raises(IndexConformanceException, lambda: get_indices(x[i] + y[j]))


def test_scalar_broadcast():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j = Idx('i'), Idx('j')
    assert get_indices(x[i] + y[i, i]) == (set([i]), {})


def test_get_indices_add():
    x = IndexedBase('x')
    y = IndexedBase('y')
    A = IndexedBase('A')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    assert get_indices(x[i] + 2*y[i]) == (set([i, ]), {})
    assert get_indices(y[i] + 2*A[i, j]*x[j]) == (set([i, ]), {})
    assert get_indices(y[i] + 2*(x[i] + A[i, j]*x[j])) == (set([i, ]), {})
    assert get_indices(y[i] + x[i]*(A[j, j] + 1)) == (set([i, ]), {})
    assert get_indices(
        y[i] + x[i]*x[j]*(y[j] + A[j, k]*x[k])) == (set([i, ]), {})


def test_get_indices_Pow():
    x = IndexedBase('x')
    y = IndexedBase('y')
    A = IndexedBase('A')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    assert get_indices(Pow(x[i], y[j])) == (set([i, j]), {})
    assert get_indices(Pow(x[i, k], y[j, k])) == (set([i, j, k]), {})
    assert get_indices(Pow(A[i, k], y[k] + A[k, j]*x[j])) == (set([i, k]), {})
    assert get_indices(Pow(2, x[i])) == get_indices(exp(x[i]))

    # test of a design decision, this may change:
    assert get_indices(Pow(x[i], 2)) == (set([i, ]), {})


def test_get_contraction_structure_basic():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j = Idx('i'), Idx('j')
    assert get_contraction_structure(x[i]*y[j]) == {None: set([x[i]*y[j]])}
    assert get_contraction_structure(x[i] + y[j]) == {None: set([x[i], y[j]])}
    assert get_contraction_structure(x[i]*y[i]) == {(i,): set([x[i]*y[i]])}
    assert get_contraction_structure(
        1 + x[i]*y[i]) == {None: set([S.One]), (i,): set([x[i]*y[i]])}
    assert get_contraction_structure(x[i]**y[i]) == {None: set([x[i]**y[i]])}


def test_get_contraction_structure_complex():
    x = IndexedBase('x')
    y = IndexedBase('y')
    A = IndexedBase('A')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    expr1 = y[i] + A[i, j]*x[j]
    d1 = {None: set([y[i]]), (j,): set([A[i, j]*x[j]])}
    assert get_contraction_structure(expr1) == d1
    expr2 = expr1*A[k, i] + x[k]
    d2 = {None: set([x[k]]), (i,): set([expr1*A[k, i]]), expr1*A[k, i]: [d1]}
    assert get_contraction_structure(expr2) == d2


def test_contraction_structure_simple_Pow():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    ii_jj = x[i, i]**y[j, j]
    assert get_contraction_structure(ii_jj) == {
        None: set([ii_jj]),
        ii_jj: [
            {(i,): set([x[i, i]])},
            {(j,): set([y[j, j]])}
        ]
    }


def test_contraction_structure_Mul_and_Pow():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j, k = Idx('i'), Idx('j'), Idx('k')

    i_ji = x[i]**(y[j]*x[i])
    assert get_contraction_structure(i_ji) == {None: set([i_ji])}
    ij_i = (x[i]*y[j])**(y[i])
    assert get_contraction_structure(ij_i) == {None: set([ij_i])}
    j_ij_i = x[j]*(x[i]*y[j])**(y[i])
    assert get_contraction_structure(j_ij_i) == {(j,): set([j_ij_i])}
    j_i_ji = x[j]*x[i]**(y[j]*x[i])
    assert get_contraction_structure(j_i_ji) == {(j,): set([j_i_ji])}
    ij_exp_kki = x[i]*y[j]*exp(y[i]*y[k, k])
    result = get_contraction_structure(ij_exp_kki)
    expected = {
        (i,): set([ij_exp_kki]),
        ij_exp_kki: [{
                     None: set([exp(y[i]*y[k, k])]),
                exp(y[i]*y[k, k]): [{
                    None: set([y[i]*y[k, k]]),
                    y[i]*y[k, k]: [{(k,): set([y[k, k]])}]
                }]}
        ]
    }
    assert result == expected


def test_contraction_structure_Add_in_Pow():
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    s_ii_jj_s = (1 + x[i, i])**(1 + y[j, j])
    expected = {
        None: set([s_ii_jj_s]),
        s_ii_jj_s: [
            {None: set([S.One]), (i,): set([x[i, i]])},
            {None: set([S.One]), (j,): set([y[j, j]])}
        ]
    }
    result = get_contraction_structure(s_ii_jj_s)
    assert result == expected


def test_contraction_structure_Pow_in_Pow():
    x = IndexedBase('x')
    y = IndexedBase('y')
    z = IndexedBase('z')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    ii_jj_kk = x[i, i]**y[j, j]**z[k, k]
    expected = {
        None: set([ii_jj_kk]),
        ii_jj_kk: [
            {(i,): set([x[i, i]])},
            {
                None: set([y[j, j]**z[k, k]]),
                y[j, j]**z[k, k]: [
                    {(j,): set([y[j, j]])},
                    {(k,): set([z[k, k]])}
                ]
            }
        ]
    }
    assert get_contraction_structure(ii_jj_kk) == expected


def test_ufunc_support():
    f = Function('f')
    g = Function('g')
    x = IndexedBase('x')
    y = IndexedBase('y')
    i, j, k = Idx('i'), Idx('j'), Idx('k')
    a = symbols('a')

    assert get_indices(f(x[i])) == (set([i]), {})
    assert get_indices(f(x[i], y[j])) == (set([i, j]), {})
    assert get_indices(f(y[i])*g(x[i])) == (set(), {})
    assert get_indices(f(a, x[i])) == (set([i]), {})
    assert get_indices(f(a, y[i], x[j])*g(x[i])) == (set([j]), {})
    assert get_indices(g(f(x[i]))) == (set([i]), {})

    assert get_contraction_structure(f(x[i])) == {None: set([f(x[i])])}
    assert get_contraction_structure(
        f(y[i])*g(x[i])) == {(i,): set([f(y[i])*g(x[i])])}
    assert get_contraction_structure(
        f(y[i])*g(f(x[i]))) == {(i,): set([f(y[i])*g(f(x[i]))])}
    assert get_contraction_structure(
        f(x[j], y[i])*g(x[i])) == {(i,): set([f(x[j], y[i])*g(x[i])])}
