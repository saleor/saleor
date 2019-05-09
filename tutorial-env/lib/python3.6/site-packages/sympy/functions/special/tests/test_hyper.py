from sympy import (hyper, meijerg, S, Tuple, pi, I, exp, log,
                   cos, sqrt, symbols, oo, Derivative, gamma, O, appellf1)
from sympy.series.limits import limit
from sympy.abc import x, z, k
from sympy.utilities.pytest import raises, slow
from sympy.utilities.randtest import (
    random_complex_number as randcplx,
    verify_numerically as tn,
    test_derivative_numerically as td)


def test_TupleParametersBase():
    # test that our implementation of the chain rule works
    p = hyper((), (), z**2)
    assert p.diff(z) == p*2*z


def test_hyper():
    raises(TypeError, lambda: hyper(1, 2, z))

    assert hyper((1, 2), (1,), z) == hyper(Tuple(1, 2), Tuple(1), z)

    h = hyper((1, 2), (3, 4, 5), z)
    assert h.ap == Tuple(1, 2)
    assert h.bq == Tuple(3, 4, 5)
    assert h.argument == z
    assert h.is_commutative is True

    # just a few checks to make sure that all arguments go where they should
    assert tn(hyper(Tuple(), Tuple(), z), exp(z), z)
    assert tn(z*hyper((1, 1), Tuple(2), -z), log(1 + z), z)

    # differentiation
    h = hyper(
        (randcplx(), randcplx(), randcplx()), (randcplx(), randcplx()), z)
    assert td(h, z)

    a1, a2, b1, b2, b3 = symbols('a1:3, b1:4')
    assert hyper((a1, a2), (b1, b2, b3), z).diff(z) == \
        a1*a2/(b1*b2*b3) * hyper((a1 + 1, a2 + 1), (b1 + 1, b2 + 1, b3 + 1), z)

    # differentiation wrt parameters is not supported
    assert hyper([z], [], z).diff(z) == Derivative(hyper([z], [], z), z)

    # hyper is unbranched wrt parameters
    from sympy import polar_lift
    assert hyper([polar_lift(z)], [polar_lift(k)], polar_lift(x)) == \
        hyper([z], [k], polar_lift(x))


def test_expand_func():
    # evaluation at 1 of Gauss' hypergeometric function:
    from sympy.abc import a, b, c
    from sympy import gamma, expand_func
    a1, b1, c1 = randcplx(), randcplx(), randcplx() + 5
    assert expand_func(hyper([a, b], [c], 1)) == \
        gamma(c)*gamma(-a - b + c)/(gamma(-a + c)*gamma(-b + c))
    assert abs(expand_func(hyper([a1, b1], [c1], 1)).n()
               - hyper([a1, b1], [c1], 1).n()) < 1e-10

    # hyperexpand wrapper for hyper:
    assert expand_func(hyper([], [], z)) == exp(z)
    assert expand_func(hyper([1, 2, 3], [], z)) == hyper([1, 2, 3], [], z)
    assert expand_func(meijerg([[1, 1], []], [[1], [0]], z)) == log(z + 1)
    assert expand_func(meijerg([[1, 1], []], [[], []], z)) == \
        meijerg([[1, 1], []], [[], []], z)


def replace_dummy(expr, sym):
    from sympy import Dummy
    dum = expr.atoms(Dummy)
    if not dum:
        return expr
    assert len(dum) == 1
    return expr.xreplace({dum.pop(): sym})


def test_hyper_rewrite_sum():
    from sympy import RisingFactorial, factorial, Dummy, Sum
    _k = Dummy("k")
    assert replace_dummy(hyper((1, 2), (1, 3), x).rewrite(Sum), _k) == \
        Sum(x**_k / factorial(_k) * RisingFactorial(2, _k) /
            RisingFactorial(3, _k), (_k, 0, oo))

    assert hyper((1, 2, 3), (-1, 3), z).rewrite(Sum) == \
        hyper((1, 2, 3), (-1, 3), z)


def test_radius_of_convergence():
    assert hyper((1, 2), [3], z).radius_of_convergence == 1
    assert hyper((1, 2), [3, 4], z).radius_of_convergence == oo
    assert hyper((1, 2, 3), [4], z).radius_of_convergence == 0
    assert hyper((0, 1, 2), [4], z).radius_of_convergence == oo
    assert hyper((-1, 1, 2), [-4], z).radius_of_convergence == 0
    assert hyper((-1, -2, 2), [-1], z).radius_of_convergence == oo
    assert hyper((-1, 2), [-1, -2], z).radius_of_convergence == 0
    assert hyper([-1, 1, 3], [-2, 2], z).radius_of_convergence == 1
    assert hyper([-1, 1], [-2, 2], z).radius_of_convergence == oo
    assert hyper([-1, 1, 3], [-2], z).radius_of_convergence == 0
    assert hyper((-1, 2, 3, 4), [], z).radius_of_convergence == oo

    assert hyper([1, 1], [3], 1).convergence_statement == True
    assert hyper([1, 1], [2], 1).convergence_statement == False
    assert hyper([1, 1], [2], -1).convergence_statement == True
    assert hyper([1, 1], [1], -1).convergence_statement == False


def test_meijer():
    raises(TypeError, lambda: meijerg(1, z))
    raises(TypeError, lambda: meijerg(((1,), (2,)), (3,), (4,), z))

    assert meijerg(((1, 2), (3,)), ((4,), (5,)), z) == \
        meijerg(Tuple(1, 2), Tuple(3), Tuple(4), Tuple(5), z)

    g = meijerg((1, 2), (3, 4, 5), (6, 7, 8, 9), (10, 11, 12, 13, 14), z)
    assert g.an == Tuple(1, 2)
    assert g.ap == Tuple(1, 2, 3, 4, 5)
    assert g.aother == Tuple(3, 4, 5)
    assert g.bm == Tuple(6, 7, 8, 9)
    assert g.bq == Tuple(6, 7, 8, 9, 10, 11, 12, 13, 14)
    assert g.bother == Tuple(10, 11, 12, 13, 14)
    assert g.argument == z
    assert g.nu == 75
    assert g.delta == -1
    assert g.is_commutative is True
    assert g.is_number is False
    #issue 13071
    assert meijerg([[],[]], [[S(1)/2],[0]], 1).is_number is True

    assert meijerg([1, 2], [3], [4], [5], z).delta == S(1)/2

    # just a few checks to make sure that all arguments go where they should
    assert tn(meijerg(Tuple(), Tuple(), Tuple(0), Tuple(), -z), exp(z), z)
    assert tn(sqrt(pi)*meijerg(Tuple(), Tuple(),
                               Tuple(0), Tuple(S(1)/2), z**2/4), cos(z), z)
    assert tn(meijerg(Tuple(1, 1), Tuple(), Tuple(1), Tuple(0), z),
              log(1 + z), z)

    # test exceptions
    raises(ValueError, lambda: meijerg(((3, 1), (2,)), ((oo,), (2, 0)), x))
    raises(ValueError, lambda: meijerg(((3, 1), (2,)), ((1,), (2, 0)), x))

    # differentiation
    g = meijerg((randcplx(),), (randcplx() + 2*I,), Tuple(),
                (randcplx(), randcplx()), z)
    assert td(g, z)

    g = meijerg(Tuple(), (randcplx(),), Tuple(),
                (randcplx(), randcplx()), z)
    assert td(g, z)

    g = meijerg(Tuple(), Tuple(), Tuple(randcplx()),
                Tuple(randcplx(), randcplx()), z)
    assert td(g, z)

    a1, a2, b1, b2, c1, c2, d1, d2 = symbols('a1:3, b1:3, c1:3, d1:3')
    assert meijerg((a1, a2), (b1, b2), (c1, c2), (d1, d2), z).diff(z) == \
        (meijerg((a1 - 1, a2), (b1, b2), (c1, c2), (d1, d2), z)
         + (a1 - 1)*meijerg((a1, a2), (b1, b2), (c1, c2), (d1, d2), z))/z

    assert meijerg([z, z], [], [], [], z).diff(z) == \
        Derivative(meijerg([z, z], [], [], [], z), z)

    # meijerg is unbranched wrt parameters
    from sympy import polar_lift as pl
    assert meijerg([pl(a1)], [pl(a2)], [pl(b1)], [pl(b2)], pl(z)) == \
        meijerg([a1], [a2], [b1], [b2], pl(z))

    # integrand
    from sympy.abc import a, b, c, d, s
    assert meijerg([a], [b], [c], [d], z).integrand(s) == \
        z**s*gamma(c - s)*gamma(-a + s + 1)/(gamma(b - s)*gamma(-d + s + 1))


def test_meijerg_derivative():
    assert meijerg([], [1, 1], [0, 0, x], [], z).diff(x) == \
        log(z)*meijerg([], [1, 1], [0, 0, x], [], z) \
        + 2*meijerg([], [1, 1, 1], [0, 0, x, 0], [], z)

    y = randcplx()
    a = 5  # mpmath chokes with non-real numbers, and Mod1 with floats
    assert td(meijerg([x], [], [], [], y), x)
    assert td(meijerg([x**2], [], [], [], y), x)
    assert td(meijerg([], [x], [], [], y), x)
    assert td(meijerg([], [], [x], [], y), x)
    assert td(meijerg([], [], [], [x], y), x)
    assert td(meijerg([x], [a], [a + 1], [], y), x)
    assert td(meijerg([x], [a + 1], [a], [], y), x)
    assert td(meijerg([x, a], [], [], [a + 1], y), x)
    assert td(meijerg([x, a + 1], [], [], [a], y), x)
    b = S(3)/2
    assert td(meijerg([a + 2], [b], [b - 3, x], [a], y), x)


def test_meijerg_period():
    assert meijerg([], [1], [0], [], x).get_period() == 2*pi
    assert meijerg([1], [], [], [0], x).get_period() == 2*pi
    assert meijerg([], [], [0], [], x).get_period() == 2*pi  # exp(x)
    assert meijerg(
        [], [], [0], [S(1)/2], x).get_period() == 2*pi  # cos(sqrt(x))
    assert meijerg(
        [], [], [S(1)/2], [0], x).get_period() == 4*pi  # sin(sqrt(x))
    assert meijerg([1, 1], [], [1], [0], x).get_period() == oo  # log(1 + x)


def test_hyper_unpolarify():
    from sympy import exp_polar
    a = exp_polar(2*pi*I)*x
    b = x
    assert hyper([], [], a).argument == b
    assert hyper([0], [], a).argument == a
    assert hyper([0], [0], a).argument == b
    assert hyper([0, 1], [0], a).argument == a
    assert hyper([0, 1], [0], exp_polar(2*pi*I)).argument == 1


@slow
def test_hyperrep():
    from sympy.functions.special.hyper import (HyperRep, HyperRep_atanh,
        HyperRep_power1, HyperRep_power2, HyperRep_log1, HyperRep_asin1,
        HyperRep_asin2, HyperRep_sqrts1, HyperRep_sqrts2, HyperRep_log2,
        HyperRep_cosasin, HyperRep_sinasin)
    # First test the base class works.
    from sympy import Piecewise, exp_polar
    a, b, c, d, z = symbols('a b c d z')

    class myrep(HyperRep):
        @classmethod
        def _expr_small(cls, x):
            return a

        @classmethod
        def _expr_small_minus(cls, x):
            return b

        @classmethod
        def _expr_big(cls, x, n):
            return c*n

        @classmethod
        def _expr_big_minus(cls, x, n):
            return d*n
    assert myrep(z).rewrite('nonrep') == Piecewise((0, abs(z) > 1), (a, True))
    assert myrep(exp_polar(I*pi)*z).rewrite('nonrep') == \
        Piecewise((0, abs(z) > 1), (b, True))
    assert myrep(exp_polar(2*I*pi)*z).rewrite('nonrep') == \
        Piecewise((c, abs(z) > 1), (a, True))
    assert myrep(exp_polar(3*I*pi)*z).rewrite('nonrep') == \
        Piecewise((d, abs(z) > 1), (b, True))
    assert myrep(exp_polar(4*I*pi)*z).rewrite('nonrep') == \
        Piecewise((2*c, abs(z) > 1), (a, True))
    assert myrep(exp_polar(5*I*pi)*z).rewrite('nonrep') == \
        Piecewise((2*d, abs(z) > 1), (b, True))
    assert myrep(z).rewrite('nonrepsmall') == a
    assert myrep(exp_polar(I*pi)*z).rewrite('nonrepsmall') == b

    def t(func, hyp, z):
        """ Test that func is a valid representation of hyp. """
        # First test that func agrees with hyp for small z
        if not tn(func.rewrite('nonrepsmall'), hyp, z,
                  a=S(-1)/2, b=S(-1)/2, c=S(1)/2, d=S(1)/2):
            return False
        # Next check that the two small representations agree.
        if not tn(
            func.rewrite('nonrepsmall').subs(
                z, exp_polar(I*pi)*z).replace(exp_polar, exp),
            func.subs(z, exp_polar(I*pi)*z).rewrite('nonrepsmall'),
                z, a=S(-1)/2, b=S(-1)/2, c=S(1)/2, d=S(1)/2):
            return False
        # Next check continuity along exp_polar(I*pi)*t
        expr = func.subs(z, exp_polar(I*pi)*z).rewrite('nonrep')
        if abs(expr.subs(z, 1 + 1e-15).n() - expr.subs(z, 1 - 1e-15).n()) > 1e-10:
            return False
        # Finally check continuity of the big reps.

        def dosubs(func, a, b):
            rv = func.subs(z, exp_polar(a)*z).rewrite('nonrep')
            return rv.subs(z, exp_polar(b)*z).replace(exp_polar, exp)
        for n in [0, 1, 2, 3, 4, -1, -2, -3, -4]:
            expr1 = dosubs(func, 2*I*pi*n, I*pi/2)
            expr2 = dosubs(func, 2*I*pi*n + I*pi, -I*pi/2)
            if not tn(expr1, expr2, z):
                return False
            expr1 = dosubs(func, 2*I*pi*(n + 1), -I*pi/2)
            expr2 = dosubs(func, 2*I*pi*n + I*pi, I*pi/2)
            if not tn(expr1, expr2, z):
                return False
        return True

    # Now test the various representatives.
    a = S(1)/3
    assert t(HyperRep_atanh(z), hyper([S(1)/2, 1], [S(3)/2], z), z)
    assert t(HyperRep_power1(a, z), hyper([-a], [], z), z)
    assert t(HyperRep_power2(a, z), hyper([a, a - S(1)/2], [2*a], z), z)
    assert t(HyperRep_log1(z), -z*hyper([1, 1], [2], z), z)
    assert t(HyperRep_asin1(z), hyper([S(1)/2, S(1)/2], [S(3)/2], z), z)
    assert t(HyperRep_asin2(z), hyper([1, 1], [S(3)/2], z), z)
    assert t(HyperRep_sqrts1(a, z), hyper([-a, S(1)/2 - a], [S(1)/2], z), z)
    assert t(HyperRep_sqrts2(a, z),
             -2*z/(2*a + 1)*hyper([-a - S(1)/2, -a], [S(1)/2], z).diff(z), z)
    assert t(HyperRep_log2(z), -z/4*hyper([S(3)/2, 1, 1], [2, 2], z), z)
    assert t(HyperRep_cosasin(a, z), hyper([-a, a], [S(1)/2], z), z)
    assert t(HyperRep_sinasin(a, z), 2*a*z*hyper([1 - a, 1 + a], [S(3)/2], z), z)


@slow
def test_meijerg_eval():
    from sympy import besseli, exp_polar
    from sympy.abc import l
    a = randcplx()
    arg = x*exp_polar(k*pi*I)
    expr1 = pi*meijerg([[], [(a + 1)/2]], [[a/2], [-a/2, (a + 1)/2]], arg**2/4)
    expr2 = besseli(a, arg)

    # Test that the two expressions agree for all arguments.
    for x_ in [0.5, 1.5]:
        for k_ in [0.0, 0.1, 0.3, 0.5, 0.8, 1, 5.751, 15.3]:
            assert abs((expr1 - expr2).n(subs={x: x_, k: k_})) < 1e-10
            assert abs((expr1 - expr2).n(subs={x: x_, k: -k_})) < 1e-10

    # Test continuity independently
    eps = 1e-13
    expr2 = expr1.subs(k, l)
    for x_ in [0.5, 1.5]:
        for k_ in [0.5, S(1)/3, 0.25, 0.75, S(2)/3, 1.0, 1.5]:
            assert abs((expr1 - expr2).n(
                       subs={x: x_, k: k_ + eps, l: k_ - eps})) < 1e-10
            assert abs((expr1 - expr2).n(
                       subs={x: x_, k: -k_ + eps, l: -k_ - eps})) < 1e-10

    expr = (meijerg(((0.5,), ()), ((0.5, 0, 0.5), ()), exp_polar(-I*pi)/4)
            + meijerg(((0.5,), ()), ((0.5, 0, 0.5), ()), exp_polar(I*pi)/4)) \
        /(2*sqrt(pi))
    assert (expr - pi/exp(1)).n(chop=True) == 0


def test_limits():
    k, x = symbols('k, x')
    assert hyper((1,), (S(4)/3, S(5)/3), k**2).series(k) == \
           hyper((1,), (S(4)/3, S(5)/3), 0) + \
           9*k**2*hyper((2,), (S(7)/3, S(8)/3), 0)/20 + \
           81*k**4*hyper((3,), (S(10)/3, S(11)/3), 0)/1120 + \
           O(k**6) # issue 6350
    assert limit(meijerg((), (), (1,), (0,), -x), x, 0) == \
            meijerg(((), ()), ((1,), (0,)), 0) # issue 6052

def test_appellf1():
    a, b1, b2, c, x, y = symbols('a b1 b2 c x y')
    assert appellf1(a, b2, b1, c, y, x) == appellf1(a, b1, b2, c, x, y)
    assert appellf1(a, b1, b1, c, y, x) == appellf1(a, b1, b1, c, x, y)
    assert appellf1(a, b1, b2, c, S(0), S(0)) == S(1)

def test_derivative_appellf1():
    from sympy import diff
    a, b1, b2, c, x, y, z = symbols('a b1 b2 c x y z')
    assert diff(appellf1(a, b1, b2, c, x, y), x) == a*b1*appellf1(a + 1, b2, b1 + 1, c + 1, y, x)/c
    assert diff(appellf1(a, b1, b2, c, x, y), y) == a*b2*appellf1(a + 1, b1, b2 + 1, c + 1, x, y)/c
    assert diff(appellf1(a, b1, b2, c, x, y), z) == 0
    assert diff(appellf1(a, b1, b2, c, x, y), a) ==  Derivative(appellf1(a, b1, b2, c, x, y), a)
