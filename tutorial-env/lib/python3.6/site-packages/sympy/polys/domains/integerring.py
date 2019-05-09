"""Implementation of :class:`IntegerRing` class. """

from __future__ import print_function, division

from sympy.polys.domains.characteristiczero import CharacteristicZero
from sympy.polys.domains.ring import Ring
from sympy.polys.domains.simpledomain import SimpleDomain
from sympy.utilities import public

import math

@public
class IntegerRing(Ring, CharacteristicZero, SimpleDomain):
    """General class for integer rings. """

    rep = 'ZZ'

    is_IntegerRing = is_ZZ = True
    is_Numerical = True
    is_PID = True

    has_assoc_Ring = True
    has_assoc_Field = True

    def get_field(self):
        """Returns a field associated with ``self``. """
        from sympy.polys.domains import QQ
        return QQ

    def algebraic_field(self, *extension):
        r"""Returns an algebraic field, i.e. `\mathbb{Q}(\alpha, \ldots)`. """
        return self.get_field().algebraic_field(*extension)

    def from_AlgebraicField(K1, a, K0):
        """Convert a ``ANP`` object to ``dtype``. """
        if a.is_ground:
            return K1.convert(a.LC(), K0.dom)

    def log(self, a, b):
        """Returns b-base logarithm of ``a``. """
        return self.dtype(math.log(int(a), b))
