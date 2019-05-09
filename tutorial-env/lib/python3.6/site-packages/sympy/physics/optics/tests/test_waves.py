from sympy import (symbols, Symbol, pi, sqrt, cos, sin, Derivative,
    Function, simplify, I, atan2)
from sympy.abc import epsilon, mu
from sympy.functions.elementary.exponential import exp
from sympy.physics.units import speed_of_light, m, s
from sympy.physics.optics import TWave

from sympy.utilities.pytest import raises

c = speed_of_light.convert_to(m/s)


def test_twave():
    A1, phi1, A2, phi2, f = symbols('A1, phi1, A2, phi2, f')
    n = Symbol('n')  # Refractive index
    t = Symbol('t')  # Time
    x = Symbol('x')  # Spatial variable
    k = Symbol('k')  # Wavenumber
    E = Function('E')
    w1 = TWave(A1, f, phi1)
    w2 = TWave(A2, f, phi2)
    assert w1.amplitude == A1
    assert w1.frequency == f
    assert w1.phase == phi1
    assert w1.wavelength == c/(f*n)
    assert w1.time_period == 1/f
    assert w1.angular_velocity == 2*pi*f
    assert w1.wavenumber == 2*pi*f*n/c
    assert w1.speed == c/n
    w3 = w1 + w2
    assert w3.amplitude == sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2) + A2**2)
    assert w3.frequency == f
    assert w3.phase == atan2(A1*cos(phi1) + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2))
    assert w3.wavelength == c/(f*n)
    assert w3.time_period == 1/f
    assert w3.angular_velocity == 2*pi*f
    assert w3.wavenumber == 2*pi*f*n/c
    assert w3.speed == c/n
    assert simplify(w3.rewrite(sin) - sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2)
    + A2**2)*sin(pi*f*n*x*s/(149896229*m) - 2*pi*f*t + atan2(A1*cos(phi1)
    + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2)) + pi/2)) == 0
    assert w3.rewrite('pde') == epsilon*mu*Derivative(E(x, t), t, t) + Derivative(E(x, t), x, x)
    assert w3.rewrite(cos) == sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2)
    + A2**2)*cos(pi*f*n*x*s/(149896229*m) - 2*pi*f*t + atan2(A1*cos(phi1)
    + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2)))
    assert w3.rewrite(exp) == sqrt(A1**2 + 2*A1*A2*cos(phi1 - phi2)
    + A2**2)*exp(I*(pi*f*n*x*s/(149896229*m) - 2*pi*f*t
    + atan2(A1*cos(phi1) + A2*cos(phi2), A1*sin(phi1) + A2*sin(phi2))))
    w4 = TWave(A1, None, 0, 1/f)
    assert w4.frequency == f
    raises(ValueError, lambda:TWave(A1))
    raises(ValueError, lambda:TWave(A1, f, phi1, t))
