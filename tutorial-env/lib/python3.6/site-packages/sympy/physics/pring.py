from __future__ import print_function, division
from sympy import sqrt, exp, S, pi, I
from sympy.physics.quantum.constants import hbar


def wavefunction(n, x):
    """
    Returns the wavefunction for particle on ring.

    n is the quantum number, x is the angle,
    here n can be positive as well as negative
    which can be used to describe the direction of motion of particle

    Examples
    ========

    >>> from sympy.physics.pring import wavefunction, energy
    >>> from sympy import Symbol, integrate, pi
    >>> x=Symbol("x")
    >>> wavefunction(1, x)
    sqrt(2)*exp(I*x)/(2*sqrt(pi))
    >>> wavefunction(2, x)
    sqrt(2)*exp(2*I*x)/(2*sqrt(pi))
    >>> wavefunction(3, x)
    sqrt(2)*exp(3*I*x)/(2*sqrt(pi))

    The normalization of the wavefunction is:

    >>> integrate(wavefunction(2, x)*wavefunction(-2, x), (x, 0, 2*pi))
    1
    >>> integrate(wavefunction(4, x)*wavefunction(-4, x), (x, 0, 2*pi))
    1

    References
    ==========

    .. [1] Atkins, Peter W.; Friedman, Ronald (2005). Molecular Quantum
           Mechanics (4th ed.).  Pages 71-73.

    """
    # sympify arguments
    n, x = S(n), S(x)
    return exp(n * I * x) / sqrt(2 * pi)


def energy(n, m, r):
    """
    Returns the energy of the state corresponding to quantum number n.

    E=(n**2 * (hcross)**2) / (2 * m * r**2)
    here n is the quantum number, m is the mass of the particle
    and r is the radius of circle.

    Examples
    ========

    >>> from sympy.physics.pring import energy
    >>> from sympy import Symbol
    >>> m=Symbol("m")
    >>> r=Symbol("r")
    >>> energy(1, m, r)
    hbar**2/(2*m*r**2)
    >>> energy(2, m, r)
    2*hbar**2/(m*r**2)
    >>> energy(-2, 2.0, 3.0)
    0.111111111111111*hbar**2

    References
    ==========

    .. [1] Atkins, Peter W.; Friedman, Ronald (2005). Molecular Quantum
           Mechanics (4th ed.).  Pages 71-73.

    """
    n, m, r = S(n), S(m), S(r)
    if n.is_integer:
        return (n**2 * hbar**2) / (2 * m * r**2)
    else:
        raise ValueError("'n' must be integer")
