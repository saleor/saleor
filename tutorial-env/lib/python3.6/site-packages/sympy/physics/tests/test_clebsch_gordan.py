from sympy import S, sqrt, pi, Dummy, Sum, Ynm, symbols
from sympy.physics.wigner import (clebsch_gordan, wigner_9j, wigner_6j, gaunt,
        racah, dot_rot_grad_Ynm, Wigner3j, wigner_3j)
from sympy.core.numbers import Rational

# for test cases, refer : https://en.wikipedia.org/wiki/Table_of_Clebsch%E2%80%93Gordan_coefficients

def test_clebsch_gordan_docs():
    assert clebsch_gordan(S(3)/2, S(1)/2, 2, S(3)/2, S(1)/2, 2) == 1
    assert clebsch_gordan(S(3)/2, S(1)/2, 1, S(3)/2, -S(1)/2, 1) == sqrt(3)/2
    assert clebsch_gordan(S(3)/2, S(1)/2, 1, -S(1)/2, S(1)/2, 0) == -sqrt(2)/2


def test_clebsch_gordan1():
    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 1
    j = 1
    m_1 = S(1)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = -1
    j = 1
    m_1 = -S(1)/2
    m_2 = -S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 0
    j = 1
    m_1 = S(1)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 0

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 0
    j = 1
    m_1 = S(1)/2
    m_2 = -S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(2)/2

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 0
    j = 0
    m_1 = S(1)/2
    m_2 = -S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(2)/2

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 0
    j = 1
    m_1 = -S(1)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(2)/2

    j_1 = S(1)/2
    j_2 = S(1)/2
    m = 0
    j = 0
    m_1 = -S(1)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == -sqrt(2)/2

def test_clebsch_gordan2():
    j_1 = S(1)
    j_2 = S(1)/2
    m = S(3)/2
    j = S(3)/2
    m_1 = 1
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1

    j_1 = S(1)
    j_2 = S(1)/2
    m = S(1)/2
    j = S(3)/2
    m_1 = 1
    m_2 = -S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(3)

    j_1 = S(1)
    j_2 = S(1)/2
    m = S(1)/2
    j = S(1)/2
    m_1 = 1
    m_2 = -S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(2)/sqrt(3)

    j_1 = S(1)
    j_2 = S(1)/2
    m = S(1)/2
    j = S(1)/2
    m_1 = 0
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == -1/sqrt(3)

    j_1 = S(1)
    j_2 = S(1)/2
    m = S(1)/2
    j = S(3)/2
    m_1 = 0
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(2)/sqrt(3)

    j_1 = S(1)
    j_2 = S(1)
    m = S(2)
    j = S(2)
    m_1 = 1
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1


    j_1 = S(1)
    j_2 = S(1)
    m = 1
    j = S(2)
    m_1 = 1
    m_2 = 0
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)


    j_1 = S(1)
    j_2 = S(1)
    m = 1
    j = S(2)
    m_1 = 0
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)

    j_1 = S(1)
    j_2 = S(1)
    m = 1
    j = 1
    m_1 = 1
    m_2 = 0
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)

    j_1 = S(1)
    j_2 = S(1)
    m = 1
    j = 1
    m_1 = 0
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == -1/sqrt(2)

def test_clebsch_gordan3():
    j_1 = S(3)/2
    j_2 = S(3)/2
    m = S(3)
    j = S(3)
    m_1 = S(3)/2
    m_2 = S(3)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1


    j_1 = S(3)/2
    j_2 = S(3)/2
    m = S(2)
    j = S(2)
    m_1 = S(3)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)

    j_1 = S(3)/2
    j_2 = S(3)/2
    m = S(2)
    j = S(3)
    m_1 = S(3)/2
    m_2 = S(1)/2
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)

def test_clebsch_gordan4():
    j_1 = S(2)
    j_2 = S(2)
    m = S(4)
    j = S(4)
    m_1 = S(2)
    m_2 = S(2)
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1


    j_1 = S(2)
    j_2 = S(2)
    m = S(3)
    j = S(3)
    m_1 = S(2)
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(2)

    j_1 = S(2)
    j_2 = S(2)
    m = S(2)
    j = S(3)
    m_1 = 1
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 0

def test_clebsch_gordan5():
    j_1 = S(5)/2
    j_2 = S(1)
    m = S(7)/2
    j = S(7)/2
    m_1 = S(5)/2
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1


    j_1 = S(5)/2
    j_2 = S(1)
    m = S(5)/2
    j = S(5)/2
    m_1 = S(5)/2
    m_2 = 0
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == sqrt(5)/sqrt(7)

    j_1 = S(5)/2
    j_2 = S(1)
    m = S(3)/2
    j = S(3)/2
    m_1 = S(1)/2
    m_2 = 1
    assert clebsch_gordan(j_1, j_2, j, m_1, m_2, m) == 1/sqrt(15)


def test_wigner():
    def tn(a, b):
        return (a - b).n(64) < S('1e-64')
    assert tn(wigner_9j(1, 1, 1, 1, 1, 1, 1, 1, 0, prec=64), S(1)/18)
    assert wigner_9j(3, 3, 2, 3, 3, 2, 3, 3, 2) == 3221*sqrt(
        70)/(246960*sqrt(105)) - 365/(3528*sqrt(70)*sqrt(105))
    assert wigner_6j(5, 5, 5, 5, 5, 5) == Rational(1, 52)
    assert tn(wigner_6j(8, 8, 8, 8, 8, 8, prec=64), -S(12219)/965770)
    # regression test for #8747
    half = Rational(1, 2)
    assert wigner_9j(0, 0, 0, 0, half, half, 0, half, half) == half
    assert (wigner_9j(3, 5, 4,
                      7 * half, 5 * half, 4,
                      9 * half, 9 * half, 0)
            == -sqrt(Rational(361, 205821000)))
    assert (wigner_9j(1, 4, 3,
                      5 * half, 4, 5 * half,
                      5 * half, 2, 7 * half)
            == -sqrt(Rational(3971, 373403520)))
    assert (wigner_9j(4, 9 * half, 5 * half,
                      2, 4, 4,
                      5, 7 * half, 7 * half)
            == -sqrt(Rational(3481, 5042614500)))


def test_gaunt():
    def tn(a, b):
        return (a - b).n(64) < S('1e-64')
    assert gaunt(1, 0, 1, 1, 0, -1) == -1/(2*sqrt(pi))
    assert isinstance(gaunt(1, 1, 0, -1, 1, 0).args[0], Rational)
    assert isinstance(gaunt(0, 1, 1, 0, -1, 1).args[0], Rational)

    assert tn(gaunt(
        10, 10, 12, 9, 3, -12, prec=64), (-S(98)/62031) * sqrt(6279)/sqrt(pi))
    def gaunt_ref(l1, l2, l3, m1, m2, m3):
        return (
            sqrt((2 * l1 + 1) * (2 * l2 + 1) * (2 * l3 + 1) / (4 * pi)) *
            wigner_3j(l1, l2, l3, 0, 0, 0) *
            wigner_3j(l1, l2, l3, m1, m2, m3)
        )
    threshold = 1e-10
    l_max = 3
    l3_max = 24
    for l1 in range(l_max + 1):
        for l2 in range(l_max + 1):
            for l3 in range(l3_max + 1):
                for m1 in range(-l1, l1 + 1):
                    for m2 in range(-l2, l2 + 1):
                        for m3 in range(-l3, l3 + 1):
                            args = l1, l2, l3, m1, m2, m3
                            g  = gaunt(*args)
                            g0 = gaunt_ref(*args)
                            assert abs(g - g0) < threshold
                            if m1 + m2 + m3 != 0:
                                assert abs(g) < threshold
                            if (l1 + l2 + l3) % 2:
                                assert abs(g) < threshold


def test_racah():
    assert racah(3,3,3,3,3,3) == Rational(-1,14)
    assert racah(2,2,2,2,2,2) == Rational(-3,70)
    assert racah(7,8,7,1,7,7, prec=4).is_Float
    assert racah(5.5,7.5,9.5,6.5,8,9) == -719*sqrt(598)/1158924
    assert abs(racah(5.5,7.5,9.5,6.5,8,9, prec=4) - (-0.01517)) < S('1e-4')


def test_dot_rota_grad_SH():
    theta, phi = symbols("theta phi")
    assert dot_rot_grad_Ynm(1, 1, 1, 1, 1, 0) !=  \
        sqrt(30)*Ynm(2, 2, 1, 0)/(10*sqrt(pi))
    assert dot_rot_grad_Ynm(1, 1, 1, 1, 1, 0).doit() ==  \
        sqrt(30)*Ynm(2, 2, 1, 0)/(10*sqrt(pi))
    assert dot_rot_grad_Ynm(1, 5, 1, 1, 1, 2) !=  \
        0
    assert dot_rot_grad_Ynm(1, 5, 1, 1, 1, 2).doit() ==  \
        0
    assert dot_rot_grad_Ynm(3, 3, 3, 3, theta, phi).doit() ==  \
        15*sqrt(3003)*Ynm(6, 6, theta, phi)/(143*sqrt(pi))
    assert dot_rot_grad_Ynm(3, 3, 1, 1, theta, phi).doit() ==  \
        sqrt(3)*Ynm(4, 4, theta, phi)/sqrt(pi)
    assert dot_rot_grad_Ynm(3, 2, 2, 0, theta, phi).doit() ==  \
        3*sqrt(55)*Ynm(5, 2, theta, phi)/(11*sqrt(pi))
    assert dot_rot_grad_Ynm(3, 2, 3, 2, theta, phi).doit() ==  \
        -sqrt(70)*Ynm(4, 4, theta, phi)/(11*sqrt(pi)) + \
        45*sqrt(182)*Ynm(6, 4, theta, phi)/(143*sqrt(pi))
