"""Implementation of :class:`CompositeDomain` class. """

from __future__ import print_function, division

from sympy.polys.domains.domain import Domain
from sympy.polys.polyerrors import GeneratorsError

from sympy.utilities import public

@public
class CompositeDomain(Domain):
    """Base class for composite domains, e.g. ZZ[x], ZZ(X). """

    is_Composite = True

    gens, ngens, symbols, domain = [None]*4

    def inject(self, *symbols):
        """Inject generators into this domain. """
        if not (set(self.symbols) & set(symbols)):
            return self.__class__(self.domain, self.symbols + symbols, self.order)
        else:
            raise GeneratorsError("common generators in %s and %s" % (self.symbols, symbols))
