"""Tests for tools for constructing domains for expressions. """

from sympy.polys.constructor import construct_domain
from sympy.polys.domains import ZZ, QQ, RR, EX
from sympy.polys.domains.realfield import RealField

from sympy import S, sqrt, sin, Float, E, GoldenRatio, pi, Catalan
from sympy.abc import x, y


def test_construct_domain():
    assert construct_domain([1, 2, 3]) == (ZZ, [ZZ(1), ZZ(2), ZZ(3)])
    assert construct_domain([1, 2, 3], field=True) == (QQ, [QQ(1), QQ(2), QQ(3)])

    assert construct_domain([S(1), S(2), S(3)]) == (ZZ, [ZZ(1), ZZ(2), ZZ(3)])
    assert construct_domain([S(1), S(2), S(3)], field=True) == (QQ, [QQ(1), QQ(2), QQ(3)])

    assert construct_domain([S(1)/2, S(2)]) == (QQ, [QQ(1, 2), QQ(2)])
    result = construct_domain([3.14, 1, S(1)/2])
    assert isinstance(result[0], RealField)
    assert result[1] == [RR(3.14), RR(1.0), RR(0.5)]

    assert construct_domain([3.14, sqrt(2)], extension=None) == (EX, [EX(3.14), EX(sqrt(2))])
    assert construct_domain([3.14, sqrt(2)], extension=True) == (EX, [EX(3.14), EX(sqrt(2))])

    assert construct_domain([1, sqrt(2)], extension=None) == (EX, [EX(1), EX(sqrt(2))])

    assert construct_domain([x, sqrt(x)]) == (EX, [EX(x), EX(sqrt(x))])
    assert construct_domain([x, sqrt(x), sqrt(y)]) == (EX, [EX(x), EX(sqrt(x)), EX(sqrt(y))])

    alg = QQ.algebraic_field(sqrt(2))

    assert construct_domain([7, S(1)/2, sqrt(2)], extension=True) == \
        (alg, [alg.convert(7), alg.convert(S(1)/2), alg.convert(sqrt(2))])

    alg = QQ.algebraic_field(sqrt(2) + sqrt(3))

    assert construct_domain([7, sqrt(2), sqrt(3)], extension=True) == \
        (alg, [alg.convert(7), alg.convert(sqrt(2)), alg.convert(sqrt(3))])

    dom = ZZ[x]

    assert construct_domain([2*x, 3]) == \
        (dom, [dom.convert(2*x), dom.convert(3)])

    dom = ZZ[x, y]

    assert construct_domain([2*x, 3*y]) == \
        (dom, [dom.convert(2*x), dom.convert(3*y)])

    dom = QQ[x]

    assert construct_domain([x/2, 3]) == \
        (dom, [dom.convert(x/2), dom.convert(3)])

    dom = QQ[x, y]

    assert construct_domain([x/2, 3*y]) == \
        (dom, [dom.convert(x/2), dom.convert(3*y)])

    dom = RR[x]

    assert construct_domain([x/2, 3.5]) == \
        (dom, [dom.convert(x/2), dom.convert(3.5)])

    dom = RR[x, y]

    assert construct_domain([x/2, 3.5*y]) == \
        (dom, [dom.convert(x/2), dom.convert(3.5*y)])

    dom = ZZ.frac_field(x)

    assert construct_domain([2/x, 3]) == \
        (dom, [dom.convert(2/x), dom.convert(3)])

    dom = ZZ.frac_field(x, y)

    assert construct_domain([2/x, 3*y]) == \
        (dom, [dom.convert(2/x), dom.convert(3*y)])

    dom = RR.frac_field(x)

    assert construct_domain([2/x, 3.5]) == \
        (dom, [dom.convert(2/x), dom.convert(3.5)])

    dom = RR.frac_field(x, y)

    assert construct_domain([2/x, 3.5*y]) == \
        (dom, [dom.convert(2/x), dom.convert(3.5*y)])

    dom = RealField(prec=336)[x]

    assert construct_domain([pi.evalf(100)*x]) == \
        (dom, [dom.convert(pi.evalf(100)*x)])

    assert construct_domain(2) == (ZZ, ZZ(2))
    assert construct_domain(S(2)/3) == (QQ, QQ(2, 3))

    assert construct_domain({}) == (ZZ, {})


def test_composite_option():
    assert construct_domain({(1,): sin(y)}, composite=False) == \
        (EX, {(1,): EX(sin(y))})

    assert construct_domain({(1,): y}, composite=False) == \
        (EX, {(1,): EX(y)})

    assert construct_domain({(1, 1): 1}, composite=False) == \
        (ZZ, {(1, 1): 1})

    assert construct_domain({(1, 0): y}, composite=False) == \
        (EX, {(1, 0): EX(y)})


def test_precision():
    f1 = Float("1.01")
    f2 = Float("1.0000000000000000000001")
    for x in [1, 1e-2, 1e-6, 1e-13, 1e-14, 1e-16, 1e-20, 1e-100, 1e-300,
            f1, f2]:
        result = construct_domain([x])
        y = float(result[1][0])
        assert abs(x - y) / x < 1e-14  # Test relative accuracy

    result = construct_domain([f1])
    y = result[1][0]
    assert y-1 > 1e-50

    result = construct_domain([f2])
    y = result[1][0]
    assert y-1 > 1e-50


def test_issue_11538():
    for n in [E, pi, Catalan]:
        assert construct_domain(n)[0] == ZZ[n]
        assert construct_domain(x + n)[0] == ZZ[x, n]
    assert construct_domain(GoldenRatio)[0] == EX
    assert construct_domain(x + GoldenRatio)[0] == EX
