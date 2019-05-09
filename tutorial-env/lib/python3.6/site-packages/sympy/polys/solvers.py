"""Low-level linear systems solver. """

from __future__ import print_function, division

from sympy.matrices import Matrix, zeros

class RawMatrix(Matrix):
    _sympify = staticmethod(lambda x: x)

def eqs_to_matrix(eqs, ring):
    """Transform from equations to matrix form. """
    xs = ring.gens
    M = zeros(len(eqs), len(xs)+1, cls=RawMatrix)

    for j, e_j in enumerate(eqs):
        for i, x_i in enumerate(xs):
            M[j, i] = e_j.coeff(x_i)
        M[j, -1] = -e_j.coeff(1)

    return M

def solve_lin_sys(eqs, ring, _raw=True):
    """Solve a system of linear equations.

    If ``_raw`` is False, the keys and values in the returned dictionary
    will be of type Expr (and the unit of the field will be removed from
    the keys) otherwise the low-level polys types will be returned, e.g.
    PolyElement: PythonRational.
    """
    as_expr = not _raw

    assert ring.domain.is_Field

    # transform from equations to matrix form
    matrix = eqs_to_matrix(eqs, ring)

    # solve by row-reduction
    echelon, pivots = matrix.rref(iszerofunc=lambda x: not x, simplify=lambda x: x)

    # construct the returnable form of the solutions
    keys = ring.symbols if as_expr else ring.gens

    if pivots[-1] == len(keys):
        return None

    if len(pivots) == len(keys):
        sol = []
        for s in echelon[:, -1]:
            a = ring.ground_new(s)
            if as_expr:
                a = a.as_expr()
            sol.append(a)
        sols = dict(zip(keys, sol))
    else:
        sols = {}
        g = ring.gens
        _g = [[-i] for i in g]
        for i, p in enumerate(pivots):
            vect = RawMatrix(_g[p + 1:] + [[ring.one]])
            v = (echelon[i, p + 1:]*vect)[0]
            if as_expr:
                v = v.as_expr()
            sols[keys[p]] = v

    return sols
