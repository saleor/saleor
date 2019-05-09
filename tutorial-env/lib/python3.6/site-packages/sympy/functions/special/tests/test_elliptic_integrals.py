from sympy import (S, Symbol, pi, I, oo, zoo, sin, sqrt, tan, gamma,
    atanh, hyper, meijerg, O)
from sympy.functions.special.elliptic_integrals import (elliptic_k as K,
    elliptic_f as F, elliptic_e as E, elliptic_pi as P)
from sympy.utilities.randtest import (test_derivative_numerically as td,
                                      random_complex_number as randcplx,
                                      verify_numerically as tn)
from sympy.abc import z, m, n

i = Symbol('i', integer=True)
j = Symbol('k', integer=True, positive=True)

def test_K():
    assert K(0) == pi/2
    assert K(S(1)/2) == 8*pi**(S(3)/2)/gamma(-S(1)/4)**2
    assert K(1) == zoo
    assert K(-1) == gamma(S(1)/4)**2/(4*sqrt(2*pi))
    assert K(oo) == 0
    assert K(-oo) == 0
    assert K(I*oo) == 0
    assert K(-I*oo) == 0
    assert K(zoo) == 0

    assert K(z).diff(z) == (E(z) - (1 - z)*K(z))/(2*z*(1 - z))
    assert td(K(z), z)

    zi = Symbol('z', real=False)
    assert K(zi).conjugate() == K(zi.conjugate())
    zr = Symbol('z', real=True, negative=True)
    assert K(zr).conjugate() == K(zr)

    assert K(z).rewrite(hyper) == \
        (pi/2)*hyper((S.Half, S.Half), (S.One,), z)
    assert tn(K(z), (pi/2)*hyper((S.Half, S.Half), (S.One,), z))
    assert K(z).rewrite(meijerg) == \
        meijerg(((S.Half, S.Half), []), ((S.Zero,), (S.Zero,)), -z)/2
    assert tn(K(z), meijerg(((S.Half, S.Half), []), ((S.Zero,), (S.Zero,)), -z)/2)

    assert K(z).series(z) == pi/2 + pi*z/8 + 9*pi*z**2/128 + \
        25*pi*z**3/512 + 1225*pi*z**4/32768 + 3969*pi*z**5/131072 + O(z**6)


def test_F():
    assert F(z, 0) == z
    assert F(0, m) == 0
    assert F(pi*i/2, m) == i*K(m)
    assert F(z, oo) == 0
    assert F(z, -oo) == 0

    assert F(-z, m) == -F(z, m)

    assert F(z, m).diff(z) == 1/sqrt(1 - m*sin(z)**2)
    assert F(z, m).diff(m) == E(z, m)/(2*m*(1 - m)) - F(z, m)/(2*m) - \
        sin(2*z)/(4*(1 - m)*sqrt(1 - m*sin(z)**2))
    r = randcplx()
    assert td(F(z, r), z)
    assert td(F(r, m), m)

    mi = Symbol('m', real=False)
    assert F(z, mi).conjugate() == F(z.conjugate(), mi.conjugate())
    mr = Symbol('m', real=True, negative=True)
    assert F(z, mr).conjugate() == F(z.conjugate(), mr)

    assert F(z, m).series(z) == \
        z + z**5*(3*m**2/40 - m/30) + m*z**3/6 + O(z**6)


def test_E():
    assert E(z, 0) == z
    assert E(0, m) == 0
    assert E(i*pi/2, m) == i*E(m)
    assert E(z, oo) == zoo
    assert E(z, -oo) == zoo
    assert E(0) == pi/2
    assert E(1) == 1
    assert E(oo) == I*oo
    assert E(-oo) == oo
    assert E(zoo) == zoo

    assert E(-z, m) == -E(z, m)

    assert E(z, m).diff(z) == sqrt(1 - m*sin(z)**2)
    assert E(z, m).diff(m) == (E(z, m) - F(z, m))/(2*m)
    assert E(z).diff(z) == (E(z) - K(z))/(2*z)
    r = randcplx()
    assert td(E(r, m), m)
    assert td(E(z, r), z)
    assert td(E(z), z)

    mi = Symbol('m', real=False)
    assert E(z, mi).conjugate() == E(z.conjugate(), mi.conjugate())
    assert E(mi).conjugate() == E(mi.conjugate())
    mr = Symbol('m', real=True, negative=True)
    assert E(z, mr).conjugate() == E(z.conjugate(), mr)
    assert E(mr).conjugate() == E(mr)

    assert E(z).rewrite(hyper) == (pi/2)*hyper((-S.Half, S.Half), (S.One,), z)
    assert tn(E(z), (pi/2)*hyper((-S.Half, S.Half), (S.One,), z))
    assert E(z).rewrite(meijerg) == \
        -meijerg(((S.Half, S(3)/2), []), ((S.Zero,), (S.Zero,)), -z)/4
    assert tn(E(z), -meijerg(((S.Half, S(3)/2), []), ((S.Zero,), (S.Zero,)), -z)/4)

    assert E(z, m).series(z) == \
        z + z**5*(-m**2/40 + m/30) - m*z**3/6 + O(z**6)
    assert E(z).series(z) == pi/2 - pi*z/8 - 3*pi*z**2/128 - \
        5*pi*z**3/512 - 175*pi*z**4/32768 - 441*pi*z**5/131072 + O(z**6)


def test_P():
    assert P(0, z, m) == F(z, m)
    assert P(1, z, m) == F(z, m) + \
        (sqrt(1 - m*sin(z)**2)*tan(z) - E(z, m))/(1 - m)
    assert P(n, i*pi/2, m) == i*P(n, m)
    assert P(n, z, 0) == atanh(sqrt(n - 1)*tan(z))/sqrt(n - 1)
    assert P(n, z, n) == F(z, n) - P(1, z, n) + tan(z)/sqrt(1 - n*sin(z)**2)
    assert P(oo, z, m) == 0
    assert P(-oo, z, m) == 0
    assert P(n, z, oo) == 0
    assert P(n, z, -oo) == 0
    assert P(0, m) == K(m)
    assert P(1, m) == zoo
    assert P(n, 0) == pi/(2*sqrt(1 - n))
    assert P(2, 1) == -oo
    assert P(-1, 1) == oo
    assert P(n, n) == E(n)/(1 - n)

    assert P(n, -z, m) == -P(n, z, m)

    ni, mi = Symbol('n', real=False), Symbol('m', real=False)
    assert P(ni, z, mi).conjugate() == \
        P(ni.conjugate(), z.conjugate(), mi.conjugate())
    nr, mr = Symbol('n', real=True, negative=True), \
        Symbol('m', real=True, negative=True)
    assert P(nr, z, mr).conjugate() == P(nr, z.conjugate(), mr)
    assert P(n, m).conjugate() == P(n.conjugate(), m.conjugate())

    assert P(n, z, m).diff(n) == (E(z, m) + (m - n)*F(z, m)/n +
        (n**2 - m)*P(n, z, m)/n - n*sqrt(1 -
            m*sin(z)**2)*sin(2*z)/(2*(1 - n*sin(z)**2)))/(2*(m - n)*(n - 1))
    assert P(n, z, m).diff(z) == 1/(sqrt(1 - m*sin(z)**2)*(1 - n*sin(z)**2))
    assert P(n, z, m).diff(m) == (E(z, m)/(m - 1) + P(n, z, m) -
        m*sin(2*z)/(2*(m - 1)*sqrt(1 - m*sin(z)**2)))/(2*(n - m))
    assert P(n, m).diff(n) == (E(m) + (m - n)*K(m)/n +
        (n**2 - m)*P(n, m)/n)/(2*(m - n)*(n - 1))
    assert P(n, m).diff(m) == (E(m)/(m - 1) + P(n, m))/(2*(n - m))
    rx, ry = randcplx(), randcplx()
    assert td(P(n, rx, ry), n)
    assert td(P(rx, z, ry), z)
    assert td(P(rx, ry, m), m)

    assert P(n, z, m).series(z) == z + z**3*(m/6 + n/3) + \
        z**5*(3*m**2/40 + m*n/10 - m/30 + n**2/5 - n/15) + O(z**6)
