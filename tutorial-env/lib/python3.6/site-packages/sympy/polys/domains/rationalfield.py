"""Implementation of :class:`RationalField` class. """

from __future__ import print_function, division

from sympy.polys.domains.characteristiczero import CharacteristicZero
from sympy.polys.domains.field import Field
from sympy.polys.domains.simpledomain import SimpleDomain
from sympy.utilities import public

@public
class RationalField(Field, CharacteristicZero, SimpleDomain):
    """General class for rational fields. """

    rep = 'QQ'

    is_RationalField = is_QQ = True
    is_Numerical = True

    has_assoc_Ring = True
    has_assoc_Field = True

    def algebraic_field(self, *extension):
        r"""Returns an algebraic field, i.e. `\mathbb{Q}(\alpha, \ldots)`. """
        from sympy.polys.domains import AlgebraicField
        return AlgebraicField(self, *extension)

    def from_AlgebraicField(K1, a, K0):
        """Convert a ``ANP`` object to ``dtype``. """
        if a.is_ground:
            return K1.convert(a.LC(), K0.dom)
