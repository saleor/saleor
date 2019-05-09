"""Implementation of :class:`PythonFiniteField` class. """

from __future__ import print_function, division

from sympy.polys.domains.finitefield import FiniteField
from sympy.polys.domains.pythonintegerring import PythonIntegerRing

from sympy.utilities import public

@public
class PythonFiniteField(FiniteField):
    """Finite field based on Python's integers. """

    alias = 'FF_python'

    def __init__(self, mod, symmetric=True):
        return super(PythonFiniteField, self).__init__(mod, PythonIntegerRing(), symmetric)
