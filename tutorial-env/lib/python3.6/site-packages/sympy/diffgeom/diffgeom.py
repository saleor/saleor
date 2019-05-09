from __future__ import print_function, division

from itertools import permutations

from sympy.combinatorics import Permutation
from sympy.core import AtomicExpr, Basic, Expr, Dummy, Function, sympify, diff, Pow, Mul, Add, symbols, Tuple
from sympy.core.compatibility import range, reduce
from sympy.core.numbers import Zero
from sympy.functions import factorial
from sympy.matrices import Matrix
from sympy.simplify import simplify
from sympy.solvers import solve


# TODO you are a bit excessive in the use of Dummies
# TODO dummy point, literal field
# TODO too often one needs to call doit or simplify on the output, check the
# tests and find out why
from sympy.tensor.array import ImmutableDenseNDimArray


class Manifold(Basic):
    """Object representing a mathematical manifold.

    The only role that this object plays is to keep a list of all patches
    defined on the manifold. It does not provide any means to study the
    topological characteristics of the manifold that it represents.

    """
    def __new__(cls, name, dim):
        name = sympify(name)
        dim = sympify(dim)
        obj = Basic.__new__(cls, name, dim)
        obj.name = name
        obj.dim = dim
        obj.patches = []
        # The patches list is necessary if a Patch instance needs to enumerate
        # other Patch instance on the same manifold.
        return obj

    def _latex(self, printer, *args):
        return r'\text{%s}' % self.name


class Patch(Basic):
    """Object representing a patch on a manifold.

    On a manifold one can have many patches that do not always include the
    whole manifold. On these patches coordinate charts can be defined that
    permit the parameterization of any point on the patch in terms of a tuple
    of real numbers (the coordinates).

    This object serves as a container/parent for all coordinate system charts
    that can be defined on the patch it represents.

    Examples
    ========

    Define a Manifold and a Patch on that Manifold:

    >>> from sympy.diffgeom import Manifold, Patch
    >>> m = Manifold('M', 3)
    >>> p = Patch('P', m)
    >>> p in m.patches
    True

    """
    # Contains a reference to the parent manifold in order to be able to access
    # other patches.
    def __new__(cls, name, manifold):
        name = sympify(name)
        obj = Basic.__new__(cls, name, manifold)
        obj.name = name
        obj.manifold = manifold
        obj.manifold.patches.append(obj)
        obj.coord_systems = []
        # The list of coordinate systems is necessary for an instance of
        # CoordSystem to enumerate other coord systems on the patch.
        return obj

    @property
    def dim(self):
        return self.manifold.dim

    def _latex(self, printer, *args):
        return r'\text{%s}_{%s}' % (self.name, self.manifold._latex(printer, *args))


class CoordSystem(Basic):
    """Contains all coordinate transformation logic.

    Examples
    ========

    Define a Manifold and a Patch, and then define two coord systems on that
    patch:

    >>> from sympy import symbols, sin, cos, pi
    >>> from sympy.diffgeom import Manifold, Patch, CoordSystem
    >>> from sympy.simplify import simplify
    >>> r, theta = symbols('r, theta')
    >>> m = Manifold('M', 2)
    >>> patch = Patch('P', m)
    >>> rect = CoordSystem('rect', patch)
    >>> polar = CoordSystem('polar', patch)
    >>> rect in patch.coord_systems
    True

    Connect the coordinate systems. An inverse transformation is automatically
    found by ``solve`` when possible:

    >>> polar.connect_to(rect, [r, theta], [r*cos(theta), r*sin(theta)])
    >>> polar.coord_tuple_transform_to(rect, [0, 2])
    Matrix([
    [0],
    [0]])
    >>> polar.coord_tuple_transform_to(rect, [2, pi/2])
    Matrix([
    [0],
    [2]])
    >>> rect.coord_tuple_transform_to(polar, [1, 1]).applyfunc(simplify)
    Matrix([
    [sqrt(2)],
    [   pi/4]])

    Calculate the jacobian of the polar to cartesian transformation:

    >>> polar.jacobian(rect, [r, theta])
    Matrix([
    [cos(theta), -r*sin(theta)],
    [sin(theta),  r*cos(theta)]])

    Define a point using coordinates in one of the coordinate systems:

    >>> p = polar.point([1, 3*pi/4])
    >>> rect.point_to_coords(p)
    Matrix([
    [-sqrt(2)/2],
    [ sqrt(2)/2]])

    Define a basis scalar field (i.e. a coordinate function), that takes a
    point and returns its coordinates. It is an instance of ``BaseScalarField``.

    >>> rect.coord_function(0)(p)
    -sqrt(2)/2
    >>> rect.coord_function(1)(p)
    sqrt(2)/2

    Define a basis vector field (i.e. a unit vector field along the coordinate
    line). Vectors are also differential operators on scalar fields. It is an
    instance of ``BaseVectorField``.

    >>> v_x = rect.base_vector(0)
    >>> x = rect.coord_function(0)
    >>> v_x(x)
    1
    >>> v_x(v_x(x))
    0

    Define a basis oneform field:

    >>> dx = rect.base_oneform(0)
    >>> dx(v_x)
    1

    If you provide a list of names the fields will print nicely:
    - without provided names:

    >>> x, v_x, dx
    (rect_0, e_rect_0, drect_0)

    - with provided names

    >>> rect = CoordSystem('rect', patch, ['x', 'y'])
    >>> rect.coord_function(0), rect.base_vector(0), rect.base_oneform(0)
    (x, e_x, dx)

    """
    #  Contains a reference to the parent patch in order to be able to access
    # other coordinate system charts.
    def __new__(cls, name, patch, names=None):
        name = sympify(name)
        # names is not in args because it is related only to printing, not to
        # identifying the CoordSystem instance.
        if not names:
            names = ['%s_%d' % (name, i) for i in range(patch.dim)]
        if isinstance(names, Tuple):
            obj = Basic.__new__(cls, name, patch, names)
        else:
            names = Tuple(*symbols(names))
            obj = Basic.__new__(cls, name, patch, names)
        obj.name = name
        obj._names = [str(i) for i in names.args]
        obj.patch = patch
        obj.patch.coord_systems.append(obj)
        obj.transforms = {}
        # All the coordinate transformation logic is in this dictionary in the
        # form of:
        #  key = other coordinate system
        #  value = tuple of  # TODO make these Lambda instances
        #          - list of `Dummy` coordinates in this coordinate system
        #          - list of expressions as a function of the Dummies giving
        #          the coordinates in another coordinate system
        obj._dummies = [Dummy(str(n)) for n in names]
        obj._dummy = Dummy()
        return obj

    @property
    def dim(self):
        return self.patch.dim

    ##########################################################################
    # Coordinate transformations.
    ##########################################################################

    def connect_to(self, to_sys, from_coords, to_exprs, inverse=True, fill_in_gaps=False):
        """Register the transformation used to switch to another coordinate system.

        Parameters
        ==========

        to_sys
            another instance of ``CoordSystem``
        from_coords
            list of symbols in terms of which ``to_exprs`` is given
        to_exprs
            list of the expressions of the new coordinate tuple
        inverse
            try to deduce and register the inverse transformation
        fill_in_gaps
            try to deduce other transformation that are made
            possible by composing the present transformation with other already
            registered transformation

        """
        from_coords, to_exprs = dummyfy(from_coords, to_exprs)
        self.transforms[to_sys] = Matrix(from_coords), Matrix(to_exprs)

        if inverse:
            to_sys.transforms[self] = self._inv_transf(from_coords, to_exprs)

        if fill_in_gaps:
            self._fill_gaps_in_transformations()

    @staticmethod
    def _inv_transf(from_coords, to_exprs):
        inv_from = [i.as_dummy() for i in from_coords]
        inv_to = solve(
            [t[0] - t[1] for t in zip(inv_from, to_exprs)],
            list(from_coords), dict=True)[0]
        inv_to = [inv_to[fc] for fc in from_coords]
        return Matrix(inv_from), Matrix(inv_to)

    @staticmethod
    def _fill_gaps_in_transformations():
        raise NotImplementedError
        # TODO

    def coord_tuple_transform_to(self, to_sys, coords):
        """Transform ``coords`` to coord system ``to_sys``.

        See the docstring of ``CoordSystem`` for examples."""
        coords = Matrix(coords)
        if self != to_sys:
            transf = self.transforms[to_sys]
            coords = transf[1].subs(list(zip(transf[0], coords)))
        return coords

    def jacobian(self, to_sys, coords):
        """Return the jacobian matrix of a transformation."""
        with_dummies = self.coord_tuple_transform_to(
            to_sys, self._dummies).jacobian(self._dummies)
        return with_dummies.subs(list(zip(self._dummies, coords)))

    ##########################################################################
    # Base fields.
    ##########################################################################

    def coord_function(self, coord_index):
        """Return a ``BaseScalarField`` that takes a point and returns one of the coords.

        Takes a point and returns its coordinate in this coordinate system.

        See the docstring of ``CoordSystem`` for examples."""
        return BaseScalarField(self, coord_index)

    def coord_functions(self):
        """Returns a list of all coordinate functions.

        For more details see the ``coord_function`` method of this class."""
        return [self.coord_function(i) for i in range(self.dim)]

    def base_vector(self, coord_index):
        """Return a basis vector field.

        The basis vector field for this coordinate system. It is also an
        operator on scalar fields.

        See the docstring of ``CoordSystem`` for examples."""
        return BaseVectorField(self, coord_index)

    def base_vectors(self):
        """Returns a list of all base vectors.

        For more details see the ``base_vector`` method of this class."""
        return [self.base_vector(i) for i in range(self.dim)]

    def base_oneform(self, coord_index):
        """Return a basis 1-form field.

        The basis one-form field for this coordinate system. It is also an
        operator on vector fields.

        See the docstring of ``CoordSystem`` for examples."""
        return Differential(self.coord_function(coord_index))

    def base_oneforms(self):
        """Returns a list of all base oneforms.

        For more details see the ``base_oneform`` method of this class."""
        return [self.base_oneform(i) for i in range(self.dim)]

    ##########################################################################
    # Points.
    ##########################################################################

    def point(self, coords):
        """Create a ``Point`` with coordinates given in this coord system.

        See the docstring of ``CoordSystem`` for examples."""
        return Point(self, coords)

    def point_to_coords(self, point):
        """Calculate the coordinates of a point in this coord system.

        See the docstring of ``CoordSystem`` for examples."""
        return point.coords(self)

    ##########################################################################
    # Printing.
    ##########################################################################

    def _latex(self, printer, *args):
        return r'\text{%s}^{\text{%s}}_{%s}' % (
            self.name, self.patch.name, self.patch.manifold._latex(printer, *args))


class Point(Basic):
    """Point in a Manifold object.

    To define a point you must supply coordinates and a coordinate system.

    The usage of this object after its definition is independent of the
    coordinate system that was used in order to define it, however due to
    limitations in the simplification routines you can arrive at complicated
    expressions if you use inappropriate coordinate systems.

    Examples
    ========

    Define the boilerplate Manifold, Patch and coordinate systems:

    >>> from sympy import symbols, sin, cos, pi
    >>> from sympy.diffgeom import (
    ...        Manifold, Patch, CoordSystem, Point)
    >>> r, theta = symbols('r, theta')
    >>> m = Manifold('M', 2)
    >>> p = Patch('P', m)
    >>> rect = CoordSystem('rect', p)
    >>> polar = CoordSystem('polar', p)
    >>> polar.connect_to(rect, [r, theta], [r*cos(theta), r*sin(theta)])

    Define a point using coordinates from one of the coordinate systems:

    >>> p = Point(polar, [r, 3*pi/4])
    >>> p.coords()
    Matrix([
    [     r],
    [3*pi/4]])
    >>> p.coords(rect)
    Matrix([
    [-sqrt(2)*r/2],
    [ sqrt(2)*r/2]])

    """
    def __init__(self, coord_sys, coords):
        super(Point, self).__init__()
        self._coord_sys = coord_sys
        self._coords = Matrix(coords)
        self._args = self._coord_sys, self._coords

    def coords(self, to_sys=None):
        """Coordinates of the point in a given coordinate system.

        If ``to_sys`` is ``None`` it returns the coordinates in the system in
        which the point was defined."""
        if to_sys:
            return self._coord_sys.coord_tuple_transform_to(to_sys, self._coords)
        else:
            return self._coords

    @property
    def free_symbols(self):
        raise NotImplementedError
        return self._coords.free_symbols


class BaseScalarField(AtomicExpr):
    """Base Scalar Field over a Manifold for a given Coordinate System.

    A scalar field takes a point as an argument and returns a scalar.

    A base scalar field of a coordinate system takes a point and returns one of
    the coordinates of that point in the coordinate system in question.

    To define a scalar field you need to choose the coordinate system and the
    index of the coordinate.

    The use of the scalar field after its definition is independent of the
    coordinate system in which it was defined, however due to limitations in
    the simplification routines you may arrive at more complicated
    expression if you use unappropriate coordinate systems.

    You can build complicated scalar fields by just building up SymPy
    expressions containing ``BaseScalarField`` instances.

    Examples
    ========

    Define boilerplate Manifold, Patch and coordinate systems:

    >>> from sympy import symbols, sin, cos, pi, Function
    >>> from sympy.diffgeom import (
    ...        Manifold, Patch, CoordSystem, Point, BaseScalarField)
    >>> r0, theta0 = symbols('r0, theta0')
    >>> m = Manifold('M', 2)
    >>> p = Patch('P', m)
    >>> rect = CoordSystem('rect', p)
    >>> polar = CoordSystem('polar', p)
    >>> polar.connect_to(rect, [r0, theta0], [r0*cos(theta0), r0*sin(theta0)])

    Point to be used as an argument for the filed:

    >>> point = polar.point([r0, 0])

    Examples of fields:

    >>> fx = BaseScalarField(rect, 0)
    >>> fy = BaseScalarField(rect, 1)
    >>> (fx**2+fy**2).rcall(point)
    r0**2

    >>> g = Function('g')
    >>> ftheta = BaseScalarField(polar, 1)
    >>> fg = g(ftheta-pi)
    >>> fg.rcall(point)
    g(-pi)

    """

    is_commutative = True

    def __new__(cls, coord_sys, index):
        obj = AtomicExpr.__new__(cls, coord_sys, sympify(index))
        obj._coord_sys = coord_sys
        obj._index = index
        return obj

    def __call__(self, *args):
        """Evaluating the field at a point or doing nothing.

        If the argument is a ``Point`` instance, the field is evaluated at that
        point. The field is returned itself if the argument is any other
        object. It is so in order to have working recursive calling mechanics
        for all fields (check the ``__call__`` method of ``Expr``).
        """
        point = args[0]
        if len(args) != 1 or not isinstance(point, Point):
            return self
        coords = point.coords(self._coord_sys)
        # XXX Calling doit  is necessary with all the Subs expressions
        # XXX Calling simplify is necessary with all the trig expressions
        return simplify(coords[self._index]).doit()

    # XXX Workaround for limitations on the content of args
    free_symbols = set()

    def doit(self):
        return self


class BaseVectorField(AtomicExpr):
    r"""Vector Field over a Manifold.

    A vector field is an operator taking a scalar field and returning a
    directional derivative (which is also a scalar field).

    A base vector field is the same type of operator, however the derivation is
    specifically done with respect to a chosen coordinate.

    To define a base vector field you need to choose the coordinate system and
    the index of the coordinate.

    The use of the vector field after its definition is independent of the
    coordinate system in which it was defined, however due to limitations in the
    simplification routines you may arrive at more complicated expression if you
    use unappropriate coordinate systems.

    Examples
    ========

    Use the predefined R2 manifold, setup some boilerplate.

    >>> from sympy import symbols, pi, Function
    >>> from sympy.diffgeom.rn import R2, R2_p, R2_r
    >>> from sympy.diffgeom import BaseVectorField
    >>> from sympy import pprint
    >>> x0, y0, r0, theta0 = symbols('x0, y0, r0, theta0')

    Points to be used as arguments for the field:

    >>> point_p = R2_p.point([r0, theta0])
    >>> point_r = R2_r.point([x0, y0])

    Scalar field to operate on:

    >>> g = Function('g')
    >>> s_field = g(R2.x, R2.y)
    >>> s_field.rcall(point_r)
    g(x0, y0)
    >>> s_field.rcall(point_p)
    g(r0*cos(theta0), r0*sin(theta0))

    Vector field:

    >>> v = BaseVectorField(R2_r, 1)
    >>> pprint(v(s_field))
    /  d              \|
    |-----(g(x, xi_2))||
    \dxi_2            /|xi_2=y
    >>> pprint(v(s_field).rcall(point_r).doit())
     d
    ---(g(x0, y0))
    dy0
    >>> pprint(v(s_field).rcall(point_p))
    /  d                           \|
    |-----(g(r0*cos(theta0), xi_2))||
    \dxi_2                         /|xi_2=r0*sin(theta0)

    """

    is_commutative = False

    def __new__(cls, coord_sys, index):
        index = sympify(index)
        obj = AtomicExpr.__new__(cls, coord_sys, index)
        obj._coord_sys = coord_sys
        obj._index = index
        return obj

    def __call__(self, scalar_field):
        """Apply on a scalar field.

        The action of a vector field on a scalar field is a directional
        differentiation.

        If the argument is not a scalar field an error is raised.
        """
        if covariant_order(scalar_field) or contravariant_order(scalar_field):
            raise ValueError('Only scalar fields can be supplied as arguments to vector fields.')

        if scalar_field is None:
            return self

        base_scalars = list(scalar_field.atoms(BaseScalarField))

        # First step: e_x(x+r**2) -> e_x(x) + 2*r*e_x(r)
        d_var = self._coord_sys._dummy
        # TODO: you need a real dummy function for the next line
        d_funcs = [Function('_#_%s' % i)(d_var) for i,
                   b in enumerate(base_scalars)]
        d_result = scalar_field.subs(list(zip(base_scalars, d_funcs)))
        d_result = d_result.diff(d_var)

        # Second step: e_x(x) -> 1 and e_x(r) -> cos(atan2(x, y))
        coords = self._coord_sys._dummies
        d_funcs_deriv = [f.diff(d_var) for f in d_funcs]
        d_funcs_deriv_sub = []
        for b in base_scalars:
            jac = self._coord_sys.jacobian(b._coord_sys, coords)
            d_funcs_deriv_sub.append(jac[b._index, self._index])
        d_result = d_result.subs(list(zip(d_funcs_deriv, d_funcs_deriv_sub)))

        # Remove the dummies
        result = d_result.subs(list(zip(d_funcs, base_scalars)))
        result = result.subs(list(zip(coords, self._coord_sys.coord_functions())))
        return result.doit()


class Commutator(Expr):
    r"""Commutator of two vector fields.

    The commutator of two vector fields `v_1` and `v_2` is defined as the
    vector field `[v_1, v_2]` that evaluated on each scalar field `f` is equal
    to `v_1(v_2(f)) - v_2(v_1(f))`.

    Examples
    ========

    Use the predefined R2 manifold, setup some boilerplate.

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import Commutator
    >>> from sympy import pprint
    >>> from sympy.simplify import simplify

    Vector fields:

    >>> e_x, e_y, e_r = R2.e_x, R2.e_y, R2.e_r
    >>> c_xy = Commutator(e_x, e_y)
    >>> c_xr = Commutator(e_x, e_r)
    >>> c_xy
    0

    Unfortunately, the current code is not able to compute everything:

    >>> c_xr
    Commutator(e_x, e_r)

    >>> simplify(c_xr(R2.y**2))
    -2*y**2*cos(theta)/(x**2 + y**2)

    """
    def __new__(cls, v1, v2):
        if (covariant_order(v1) or contravariant_order(v1) != 1
                or covariant_order(v2) or contravariant_order(v2) != 1):
            raise ValueError(
                'Only commutators of vector fields are supported.')
        if v1 == v2:
            return Zero()
        coord_sys = set().union(*[v.atoms(CoordSystem) for v in (v1, v2)])
        if len(coord_sys) == 1:
            # Only one coordinate systems is used, hence it is easy enough to
            # actually evaluate the commutator.
            if all(isinstance(v, BaseVectorField) for v in (v1, v2)):
                return Zero()
            bases_1, bases_2 = [list(v.atoms(BaseVectorField))
                                for v in (v1, v2)]
            coeffs_1 = [v1.expand().coeff(b) for b in bases_1]
            coeffs_2 = [v2.expand().coeff(b) for b in bases_2]
            res = 0
            for c1, b1 in zip(coeffs_1, bases_1):
                for c2, b2 in zip(coeffs_2, bases_2):
                    res += c1*b1(c2)*b2 - c2*b2(c1)*b1
            return res
        else:
            return super(Commutator, cls).__new__(cls, v1, v2)

    def __init__(self, v1, v2):
        super(Commutator, self).__init__()
        self._args = (v1, v2)
        self._v1 = v1
        self._v2 = v2

    def __call__(self, scalar_field):
        """Apply on a scalar field.

        If the argument is not a scalar field an error is raised.
        """
        return self._v1(self._v2(scalar_field)) - self._v2(self._v1(scalar_field))


class Differential(Expr):
    r"""Return the differential (exterior derivative) of a form field.

    The differential of a form (i.e. the exterior derivative) has a complicated
    definition in the general case.

    The differential `df` of the 0-form `f` is defined for any vector field `v`
    as `df(v) = v(f)`.

    Examples
    ========

    Use the predefined R2 manifold, setup some boilerplate.

    >>> from sympy import Function
    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import Differential
    >>> from sympy import pprint

    Scalar field (0-forms):

    >>> g = Function('g')
    >>> s_field = g(R2.x, R2.y)

    Vector fields:

    >>> e_x, e_y, = R2.e_x, R2.e_y

    Differentials:

    >>> dg = Differential(s_field)
    >>> dg
    d(g(x, y))
    >>> pprint(dg(e_x))
    /  d              \|
    |-----(g(xi_1, y))||
    \dxi_1            /|xi_1=x
    >>> pprint(dg(e_y))
    /  d              \|
    |-----(g(x, xi_2))||
    \dxi_2            /|xi_2=y

    Applying the exterior derivative operator twice always results in:

    >>> Differential(dg)
    0

    """

    is_commutative = False

    def __new__(cls, form_field):
        if contravariant_order(form_field):
            raise ValueError(
                'A vector field was supplied as an argument to Differential.')
        if isinstance(form_field, Differential):
            return Zero()
        else:
            return super(Differential, cls).__new__(cls, form_field)

    def __init__(self, form_field):
        super(Differential, self).__init__()
        self._form_field = form_field
        self._args = (self._form_field, )

    def __call__(self, *vector_fields):
        """Apply on a list of vector_fields.

        If the number of vector fields supplied is not equal to 1 + the order of
        the form field inside the differential the result is undefined.

        For 1-forms (i.e. differentials of scalar fields) the evaluation is
        done as `df(v)=v(f)`. However if `v` is ``None`` instead of a vector
        field, the differential is returned unchanged. This is done in order to
        permit partial contractions for higher forms.

        In the general case the evaluation is done by applying the form field
        inside the differential on a list with one less elements than the number
        of elements in the original list. Lowering the number of vector fields
        is achieved through replacing each pair of fields by their
        commutator.

        If the arguments are not vectors or ``None``s an error is raised.
        """
        if any((contravariant_order(a) != 1 or covariant_order(a)) and a is not None
                for a in vector_fields):
            raise ValueError('The arguments supplied to Differential should be vector fields or Nones.')
        k = len(vector_fields)
        if k == 1:
            if vector_fields[0]:
                return vector_fields[0].rcall(self._form_field)
            return self
        else:
            # For higher form it is more complicated:
            # Invariant formula:
            # https://en.wikipedia.org/wiki/Exterior_derivative#Invariant_formula
            # df(v1, ... vn) = +/- vi(f(v1..no i..vn))
            #                  +/- f([vi,vj],v1..no i, no j..vn)
            f = self._form_field
            v = vector_fields
            ret = 0
            for i in range(k):
                t = v[i].rcall(f.rcall(*v[:i] + v[i + 1:]))
                ret += (-1)**i*t
                for j in range(i + 1, k):
                    c = Commutator(v[i], v[j])
                    if c:  # TODO this is ugly - the Commutator can be Zero and
                        # this causes the next line to fail
                        t = f.rcall(*(c,) + v[:i] + v[i + 1:j] + v[j + 1:])
                        ret += (-1)**(i + j)*t
            return ret


class TensorProduct(Expr):
    """Tensor product of forms.

    The tensor product permits the creation of multilinear functionals (i.e.
    higher order tensors) out of lower order fields (e.g. 1-forms and vector
    fields). However, the higher tensors thus created lack the interesting
    features provided by the other type of product, the wedge product, namely
    they are not antisymmetric and hence are not form fields.

    Examples
    ========

    Use the predefined R2 manifold, setup some boilerplate.

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import TensorProduct

    >>> TensorProduct(R2.dx, R2.dy)(R2.e_x, R2.e_y)
    1
    >>> TensorProduct(R2.dx, R2.dy)(R2.e_y, R2.e_x)
    0
    >>> TensorProduct(R2.dx, R2.x*R2.dy)(R2.x*R2.e_x, R2.e_y)
    x**2
    >>> TensorProduct(R2.e_x, R2.e_y)(R2.x**2, R2.y**2)
    4*x*y
    >>> TensorProduct(R2.e_y, R2.dx)(R2.y)
    dx


    You can nest tensor products.

    >>> tp1 = TensorProduct(R2.dx, R2.dy)
    >>> TensorProduct(tp1, R2.dx)(R2.e_x, R2.e_y, R2.e_x)
    1

    You can make partial contraction for instance when 'raising an index'.
    Putting ``None`` in the second argument of ``rcall`` means that the
    respective position in the tensor product is left as it is.

    >>> TP = TensorProduct
    >>> metric = TP(R2.dx, R2.dx) + 3*TP(R2.dy, R2.dy)
    >>> metric.rcall(R2.e_y, None)
    3*dy

    Or automatically pad the args with ``None`` without specifying them.

    >>> metric.rcall(R2.e_y)
    3*dy

    """
    def __new__(cls, *args):
        scalar = Mul(*[m for m in args if covariant_order(m) + contravariant_order(m) == 0])
        multifields = [m for m in args if covariant_order(m) + contravariant_order(m)]
        if multifields:
            if len(multifields) == 1:
                return scalar*multifields[0]
            return scalar*super(TensorProduct, cls).__new__(cls, *multifields)
        else:
            return scalar

    def __init__(self, *args):
        super(TensorProduct, self).__init__()
        self._args = args

    def __call__(self, *fields):
        """Apply on a list of fields.

        If the number of input fields supplied is not equal to the order of
        the tensor product field, the list of arguments is padded with ``None``'s.

        The list of arguments is divided in sublists depending on the order of
        the forms inside the tensor product. The sublists are provided as
        arguments to these forms and the resulting expressions are given to the
        constructor of ``TensorProduct``.
        """
        tot_order = covariant_order(self) + contravariant_order(self)
        tot_args = len(fields)
        if tot_args != tot_order:
            fields = list(fields) + [None]*(tot_order - tot_args)
        orders = [covariant_order(f) + contravariant_order(f) for f in self._args]
        indices = [sum(orders[:i + 1]) for i in range(len(orders) - 1)]
        fields = [fields[i:j] for i, j in zip([0] + indices, indices + [None])]
        multipliers = [t[0].rcall(*t[1]) for t in zip(self._args, fields)]
        return TensorProduct(*multipliers)


class WedgeProduct(TensorProduct):
    """Wedge product of forms.

    In the context of integration only completely antisymmetric forms make
    sense. The wedge product permits the creation of such forms.

    Examples
    ========

    Use the predefined R2 manifold, setup some boilerplate.

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import WedgeProduct

    >>> WedgeProduct(R2.dx, R2.dy)(R2.e_x, R2.e_y)
    1
    >>> WedgeProduct(R2.dx, R2.dy)(R2.e_y, R2.e_x)
    -1
    >>> WedgeProduct(R2.dx, R2.x*R2.dy)(R2.x*R2.e_x, R2.e_y)
    x**2
    >>> WedgeProduct(R2.e_x,R2.e_y)(R2.y,None)
    -e_x

    You can nest wedge products.

    >>> wp1 = WedgeProduct(R2.dx, R2.dy)
    >>> WedgeProduct(wp1, R2.dx)(R2.e_x, R2.e_y, R2.e_x)
    0

    """
    # TODO the calculation of signatures is slow
    # TODO you do not need all these permutations (neither the prefactor)
    def __call__(self, *fields):
        """Apply on a list of vector_fields.

        The expression is rewritten internally in terms of tensor products and evaluated."""
        orders = (covariant_order(e) + contravariant_order(e) for e in self.args)
        mul = 1/Mul(*(factorial(o) for o in orders))
        perms = permutations(fields)
        perms_par = (Permutation(
            p).signature() for p in permutations(list(range(len(fields)))))
        tensor_prod = TensorProduct(*self.args)
        return mul*Add(*[tensor_prod(*p[0])*p[1] for p in zip(perms, perms_par)])


class LieDerivative(Expr):
    """Lie derivative with respect to a vector field.

    The transport operator that defines the Lie derivative is the pushforward of
    the field to be derived along the integral curve of the field with respect
    to which one derives.

    Examples
    ========

    >>> from sympy.diffgeom import (LieDerivative, TensorProduct)
    >>> from sympy.diffgeom.rn import R2
    >>> LieDerivative(R2.e_x, R2.y)
    0
    >>> LieDerivative(R2.e_x, R2.x)
    1
    >>> LieDerivative(R2.e_x, R2.e_x)
    0

    The Lie derivative of a tensor field by another tensor field is equal to
    their commutator:

    >>> LieDerivative(R2.e_x, R2.e_r)
    Commutator(e_x, e_r)
    >>> LieDerivative(R2.e_x + R2.e_y, R2.x)
    1
    >>> tp = TensorProduct(R2.dx, R2.dy)
    >>> LieDerivative(R2.e_x, tp)
    LieDerivative(e_x, TensorProduct(dx, dy))
    >>> LieDerivative(R2.e_x, tp)
    LieDerivative(e_x, TensorProduct(dx, dy))
    """
    def __new__(cls, v_field, expr):
        expr_form_ord = covariant_order(expr)
        if contravariant_order(v_field) != 1 or covariant_order(v_field):
            raise ValueError('Lie derivatives are defined only with respect to'
                             ' vector fields. The supplied argument was not a '
                             'vector field.')
        if expr_form_ord > 0:
            return super(LieDerivative, cls).__new__(cls, v_field, expr)
        if expr.atoms(BaseVectorField):
            return Commutator(v_field, expr)
        else:
            return v_field.rcall(expr)

    def __init__(self, v_field, expr):
        super(LieDerivative, self).__init__()
        self._v_field = v_field
        self._expr = expr
        self._args = (self._v_field, self._expr)

    def __call__(self, *args):
        v = self._v_field
        expr = self._expr
        lead_term = v(expr(*args))
        rest = Add(*[Mul(*args[:i] + (Commutator(v, args[i]),) + args[i + 1:])
                     for i in range(len(args))])
        return lead_term - rest


class BaseCovarDerivativeOp(Expr):
    """Covariant derivative operator with respect to a base vector.

    Examples
    ========

    >>> from sympy.diffgeom.rn import R2, R2_r
    >>> from sympy.diffgeom import BaseCovarDerivativeOp
    >>> from sympy.diffgeom import metric_to_Christoffel_2nd, TensorProduct
    >>> TP = TensorProduct
    >>> ch = metric_to_Christoffel_2nd(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    >>> ch
    [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    >>> cvd = BaseCovarDerivativeOp(R2_r, 0, ch)
    >>> cvd(R2.x)
    1
    >>> cvd(R2.x*R2.e_x)
    e_x
    """
    def __init__(self, coord_sys, index, christoffel):
        super(BaseCovarDerivativeOp, self).__init__()
        self._coord_sys = coord_sys
        self._index = index
        self._christoffel = christoffel
        self._args = self._coord_sys, self._index, self._christoffel

    def __call__(self, field):
        """Apply on a scalar field.

        The action of a vector field on a scalar field is a directional
        differentiation.

        If the argument is not a scalar field the behaviour is undefined.
        """
        if covariant_order(field) != 0:
            raise NotImplementedError()

        field = vectors_in_basis(field, self._coord_sys)

        wrt_vector = self._coord_sys.base_vector(self._index)
        wrt_scalar = self._coord_sys.coord_function(self._index)
        vectors = list(field.atoms(BaseVectorField))

        # First step: replace all vectors with something susceptible to
        # derivation and do the derivation
        # TODO: you need a real dummy function for the next line
        d_funcs = [Function('_#_%s' % i)(wrt_scalar) for i,
                   b in enumerate(vectors)]
        d_result = field.subs(list(zip(vectors, d_funcs)))
        d_result = wrt_vector(d_result)

        # Second step: backsubstitute the vectors in
        d_result = d_result.subs(list(zip(d_funcs, vectors)))

        # Third step: evaluate the derivatives of the vectors
        derivs = []
        for v in vectors:
            d = Add(*[(self._christoffel[k, wrt_vector._index, v._index]
                       *v._coord_sys.base_vector(k))
                      for k in range(v._coord_sys.dim)])
            derivs.append(d)
        to_subs = [wrt_vector(d) for d in d_funcs]
        result = d_result.subs(list(zip(to_subs, derivs)))

        # Remove the dummies
        result = result.subs(list(zip(d_funcs, vectors)))
        return result.doit()


class CovarDerivativeOp(Expr):
    """Covariant derivative operator.

    Examples
    ========

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import CovarDerivativeOp
    >>> from sympy.diffgeom import metric_to_Christoffel_2nd, TensorProduct
    >>> TP = TensorProduct
    >>> ch = metric_to_Christoffel_2nd(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    >>> ch
    [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    >>> cvd = CovarDerivativeOp(R2.x*R2.e_x, ch)
    >>> cvd(R2.x)
    x
    >>> cvd(R2.x*R2.e_x)
    x*e_x

    """
    def __init__(self, wrt, christoffel):
        super(CovarDerivativeOp, self).__init__()
        if len(set(v._coord_sys for v in wrt.atoms(BaseVectorField))) > 1:
            raise NotImplementedError()
        if contravariant_order(wrt) != 1 or covariant_order(wrt):
            raise ValueError('Covariant derivatives are defined only with '
                             'respect to vector fields. The supplied argument '
                             'was not a vector field.')
        self._wrt = wrt
        self._christoffel = christoffel
        self._args = self._wrt, self._christoffel

    def __call__(self, field):
        vectors = list(self._wrt.atoms(BaseVectorField))
        base_ops = [BaseCovarDerivativeOp(v._coord_sys, v._index, self._christoffel)
                    for v in vectors]
        return self._wrt.subs(list(zip(vectors, base_ops))).rcall(field)

    def _latex(self, printer, *args):
        return r'\mathbb{\nabla}_{%s}' % printer._print(self._wrt)


###############################################################################
# Integral curves on vector fields
###############################################################################
def intcurve_series(vector_field, param, start_point, n=6, coord_sys=None, coeffs=False):
    r"""Return the series expansion for an integral curve of the field.

    Integral curve is a function `\gamma` taking a parameter in `R` to a point
    in the manifold. It verifies the equation:

    `V(f)\big(\gamma(t)\big) = \frac{d}{dt}f\big(\gamma(t)\big)`

    where the given ``vector_field`` is denoted as `V`. This holds for any
    value `t` for the parameter and any scalar field `f`.

    This equation can also be decomposed of a basis of coordinate functions

    `V(f_i)\big(\gamma(t)\big) = \frac{d}{dt}f_i\big(\gamma(t)\big) \quad \forall i`

    This function returns a series expansion of `\gamma(t)` in terms of the
    coordinate system ``coord_sys``. The equations and expansions are necessarily
    done in coordinate-system-dependent way as there is no other way to
    represent movement between points on the manifold (i.e. there is no such
    thing as a difference of points for a general manifold).

    See Also
    ========

    intcurve_diffequ

    Parameters
    ==========

    vector_field
        the vector field for which an integral curve will be given
    param
        the argument of the function `\gamma` from R to the curve
    start_point
        the point which corresponds to `\gamma(0)`
    n
        the order to which to expand
    coord_sys
        the coordinate system in which to expand
        coeffs (default False) - if True return a list of elements of the expansion

    Examples
    ========

    Use the predefined R2 manifold:

    >>> from sympy.abc import t, x, y
    >>> from sympy.diffgeom.rn import R2, R2_p, R2_r
    >>> from sympy.diffgeom import intcurve_series

    Specify a starting point and a vector field:

    >>> start_point = R2_r.point([x, y])
    >>> vector_field = R2_r.e_x

    Calculate the series:

    >>> intcurve_series(vector_field, t, start_point, n=3)
    Matrix([
    [t + x],
    [    y]])

    Or get the elements of the expansion in a list:

    >>> series = intcurve_series(vector_field, t, start_point, n=3, coeffs=True)
    >>> series[0]
    Matrix([
    [x],
    [y]])
    >>> series[1]
    Matrix([
    [t],
    [0]])
    >>> series[2]
    Matrix([
    [0],
    [0]])

    The series in the polar coordinate system:

    >>> series = intcurve_series(vector_field, t, start_point,
    ...             n=3, coord_sys=R2_p, coeffs=True)
    >>> series[0]
    Matrix([
    [sqrt(x**2 + y**2)],
    [      atan2(y, x)]])
    >>> series[1]
    Matrix([
    [t*x/sqrt(x**2 + y**2)],
    [   -t*y/(x**2 + y**2)]])
    >>> series[2]
    Matrix([
    [t**2*(-x**2/(x**2 + y**2)**(3/2) + 1/sqrt(x**2 + y**2))/2],
    [                                t**2*x*y/(x**2 + y**2)**2]])

    """
    if contravariant_order(vector_field) != 1 or covariant_order(vector_field):
        raise ValueError('The supplied field was not a vector field.')

    def iter_vfield(scalar_field, i):
        """Return ``vector_field`` called `i` times on ``scalar_field``."""
        return reduce(lambda s, v: v.rcall(s), [vector_field, ]*i, scalar_field)

    def taylor_terms_per_coord(coord_function):
        """Return the series for one of the coordinates."""
        return [param**i*iter_vfield(coord_function, i).rcall(start_point)/factorial(i)
                for i in range(n)]
    coord_sys = coord_sys if coord_sys else start_point._coord_sys
    coord_functions = coord_sys.coord_functions()
    taylor_terms = [taylor_terms_per_coord(f) for f in coord_functions]
    if coeffs:
        return [Matrix(t) for t in zip(*taylor_terms)]
    else:
        return Matrix([sum(c) for c in taylor_terms])


def intcurve_diffequ(vector_field, param, start_point, coord_sys=None):
    r"""Return the differential equation for an integral curve of the field.

    Integral curve is a function `\gamma` taking a parameter in `R` to a point
    in the manifold. It verifies the equation:

    `V(f)\big(\gamma(t)\big) = \frac{d}{dt}f\big(\gamma(t)\big)`

    where the given ``vector_field`` is denoted as `V`. This holds for any
    value `t` for the parameter and any scalar field `f`.

    This function returns the differential equation of `\gamma(t)` in terms of the
    coordinate system ``coord_sys``. The equations and expansions are necessarily
    done in coordinate-system-dependent way as there is no other way to
    represent movement between points on the manifold (i.e. there is no such
    thing as a difference of points for a general manifold).

    See Also
    ========

    intcurve_series

    Parameters
    ==========

    vector_field
        the vector field for which an integral curve will be given
    param
        the argument of the function `\gamma` from R to the curve
    start_point
        the point which corresponds to `\gamma(0)`
    coord_sys
        the coordinate system in which to give the equations

    Returns
    =======
    a tuple of (equations, initial conditions)

    Examples
    ========

    Use the predefined R2 manifold:

    >>> from sympy.abc import t
    >>> from sympy.diffgeom.rn import R2, R2_p, R2_r
    >>> from sympy.diffgeom import intcurve_diffequ

    Specify a starting point and a vector field:

    >>> start_point = R2_r.point([0, 1])
    >>> vector_field = -R2.y*R2.e_x + R2.x*R2.e_y

    Get the equation:

    >>> equations, init_cond = intcurve_diffequ(vector_field, t, start_point)
    >>> equations
    [f_1(t) + Derivative(f_0(t), t), -f_0(t) + Derivative(f_1(t), t)]
    >>> init_cond
    [f_0(0), f_1(0) - 1]

    The series in the polar coordinate system:

    >>> equations, init_cond = intcurve_diffequ(vector_field, t, start_point, R2_p)
    >>> equations
    [Derivative(f_0(t), t), Derivative(f_1(t), t) - 1]
    >>> init_cond
    [f_0(0) - 1, f_1(0) - pi/2]

    """
    if contravariant_order(vector_field) != 1 or covariant_order(vector_field):
        raise ValueError('The supplied field was not a vector field.')
    coord_sys = coord_sys if coord_sys else start_point._coord_sys
    gammas = [Function('f_%d' % i)(param) for i in range(
        start_point._coord_sys.dim)]
    arbitrary_p = Point(coord_sys, gammas)
    coord_functions = coord_sys.coord_functions()
    equations = [simplify(diff(cf.rcall(arbitrary_p), param) - vector_field.rcall(cf).rcall(arbitrary_p))
                 for cf in coord_functions]
    init_cond = [simplify(cf.rcall(arbitrary_p).subs(param, 0) - cf.rcall(start_point))
                 for cf in coord_functions]
    return equations, init_cond


###############################################################################
# Helpers
###############################################################################
def dummyfy(args, exprs):
    # TODO Is this a good idea?
    d_args = Matrix([s.as_dummy() for s in args])
    reps = dict(zip(args, d_args))
    d_exprs = Matrix([sympify(expr).subs(reps) for expr in exprs])
    return d_args, d_exprs


###############################################################################
# Helpers
###############################################################################
def contravariant_order(expr, _strict=False):
    """Return the contravariant order of an expression.

    Examples
    ========

    >>> from sympy.diffgeom import contravariant_order
    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.abc import a
    >>> contravariant_order(a)
    0
    >>> contravariant_order(a*R2.x + 2)
    0
    >>> contravariant_order(a*R2.x*R2.e_y + R2.e_x)
    1

    """
    # TODO move some of this to class methods.
    # TODO rewrite using the .as_blah_blah methods
    if isinstance(expr, Add):
        orders = [contravariant_order(e) for e in expr.args]
        if len(set(orders)) != 1:
            raise ValueError('Misformed expression containing contravariant fields of varying order.')
        return orders[0]
    elif isinstance(expr, Mul):
        orders = [contravariant_order(e) for e in expr.args]
        not_zero = [o for o in orders if o != 0]
        if len(not_zero) > 1:
            raise ValueError('Misformed expression containing multiplication between vectors.')
        return 0 if not not_zero else not_zero[0]
    elif isinstance(expr, Pow):
        if covariant_order(expr.base) or covariant_order(expr.exp):
            raise ValueError(
                'Misformed expression containing a power of a vector.')
        return 0
    elif isinstance(expr, BaseVectorField):
        return 1
    elif isinstance(expr, TensorProduct):
        return sum(contravariant_order(a) for a in expr.args)
    elif not _strict or expr.atoms(BaseScalarField):
        return 0
    else:  # If it does not contain anything related to the diffgeom module and it is _strict
        return -1


def covariant_order(expr, _strict=False):
    """Return the covariant order of an expression.

    Examples
    ========

    >>> from sympy.diffgeom import covariant_order
    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.abc import a
    >>> covariant_order(a)
    0
    >>> covariant_order(a*R2.x + 2)
    0
    >>> covariant_order(a*R2.x*R2.dy + R2.dx)
    1

    """
    # TODO move some of this to class methods.
    # TODO rewrite using the .as_blah_blah methods
    if isinstance(expr, Add):
        orders = [covariant_order(e) for e in expr.args]
        if len(set(orders)) != 1:
            raise ValueError('Misformed expression containing form fields of varying order.')
        return orders[0]
    elif isinstance(expr, Mul):
        orders = [covariant_order(e) for e in expr.args]
        not_zero = [o for o in orders if o != 0]
        if len(not_zero) > 1:
            raise ValueError('Misformed expression containing multiplication between forms.')
        return 0 if not not_zero else not_zero[0]
    elif isinstance(expr, Pow):
        if covariant_order(expr.base) or covariant_order(expr.exp):
            raise ValueError(
                'Misformed expression containing a power of a form.')
        return 0
    elif isinstance(expr, Differential):
        return covariant_order(*expr.args) + 1
    elif isinstance(expr, TensorProduct):
        return sum(covariant_order(a) for a in expr.args)
    elif not _strict or expr.atoms(BaseScalarField):
        return 0
    else:  # If it does not contain anything related to the diffgeom module and it is _strict
        return -1


###############################################################################
# Coordinate transformation functions
###############################################################################
def vectors_in_basis(expr, to_sys):
    """Transform all base vectors in base vectors of a specified coord basis.

    While the new base vectors are in the new coordinate system basis, any
    coefficients are kept in the old system.

    Examples
    ========

    >>> from sympy.diffgeom import vectors_in_basis
    >>> from sympy.diffgeom.rn import R2_r, R2_p
    >>> vectors_in_basis(R2_r.e_x, R2_p)
    x*e_r/sqrt(x**2 + y**2) - y*e_theta/(x**2 + y**2)
    >>> vectors_in_basis(R2_p.e_r, R2_r)
    sin(theta)*e_y + cos(theta)*e_x
    """
    vectors = list(expr.atoms(BaseVectorField))
    new_vectors = []
    for v in vectors:
        cs = v._coord_sys
        jac = cs.jacobian(to_sys, cs.coord_functions())
        new = (jac.T*Matrix(to_sys.base_vectors()))[v._index]
        new_vectors.append(new)
    return expr.subs(list(zip(vectors, new_vectors)))


###############################################################################
# Coordinate-dependent functions
###############################################################################
def twoform_to_matrix(expr):
    """Return the matrix representing the twoform.

    For the twoform `w` return the matrix `M` such that `M[i,j]=w(e_i, e_j)`,
    where `e_i` is the i-th base vector field for the coordinate system in
    which the expression of `w` is given.

    Examples
    ========

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import twoform_to_matrix, TensorProduct
    >>> TP = TensorProduct
    >>> twoform_to_matrix(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    Matrix([
    [1, 0],
    [0, 1]])
    >>> twoform_to_matrix(R2.x*TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    Matrix([
    [x, 0],
    [0, 1]])
    >>> twoform_to_matrix(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy) - TP(R2.dx, R2.dy)/2)
    Matrix([
    [   1, 0],
    [-1/2, 1]])

    """
    if covariant_order(expr) != 2 or contravariant_order(expr):
        raise ValueError('The input expression is not a two-form.')
    coord_sys = expr.atoms(CoordSystem)
    if len(coord_sys) != 1:
        raise ValueError('The input expression concerns more than one '
                         'coordinate systems, hence there is no unambiguous '
                         'way to choose a coordinate system for the matrix.')
    coord_sys = coord_sys.pop()
    vectors = coord_sys.base_vectors()
    expr = expr.expand()
    matrix_content = [[expr.rcall(v1, v2) for v1 in vectors]
                      for v2 in vectors]
    return Matrix(matrix_content)


def metric_to_Christoffel_1st(expr):
    """Return the nested list of Christoffel symbols for the given metric.

    This returns the Christoffel symbol of first kind that represents the
    Levi-Civita connection for the given metric.

    Examples
    ========

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import metric_to_Christoffel_1st, TensorProduct
    >>> TP = TensorProduct
    >>> metric_to_Christoffel_1st(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    >>> metric_to_Christoffel_1st(R2.x*TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[[1/2, 0], [0, 0]], [[0, 0], [0, 0]]]

    """
    matrix = twoform_to_matrix(expr)
    if not matrix.is_symmetric():
        raise ValueError(
            'The two-form representing the metric is not symmetric.')
    coord_sys = expr.atoms(CoordSystem).pop()
    deriv_matrices = [matrix.applyfunc(lambda a: d(a))
                      for d in coord_sys.base_vectors()]
    indices = list(range(coord_sys.dim))
    christoffel = [[[(deriv_matrices[k][i, j] + deriv_matrices[j][i, k] - deriv_matrices[i][j, k])/2
                     for k in indices]
                    for j in indices]
                   for i in indices]
    return ImmutableDenseNDimArray(christoffel)


def metric_to_Christoffel_2nd(expr):
    """Return the nested list of Christoffel symbols for the given metric.

    This returns the Christoffel symbol of second kind that represents the
    Levi-Civita connection for the given metric.

    Examples
    ========

    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import metric_to_Christoffel_2nd, TensorProduct
    >>> TP = TensorProduct
    >>> metric_to_Christoffel_2nd(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]
    >>> metric_to_Christoffel_2nd(R2.x*TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[[1/(2*x), 0], [0, 0]], [[0, 0], [0, 0]]]

    """
    ch_1st = metric_to_Christoffel_1st(expr)
    coord_sys = expr.atoms(CoordSystem).pop()
    indices = list(range(coord_sys.dim))
    # XXX workaround, inverting a matrix does not work if it contains non
    # symbols
    #matrix = twoform_to_matrix(expr).inv()
    matrix = twoform_to_matrix(expr)
    s_fields = set()
    for e in matrix:
        s_fields.update(e.atoms(BaseScalarField))
    s_fields = list(s_fields)
    dums = coord_sys._dummies
    matrix = matrix.subs(list(zip(s_fields, dums))).inv().subs(list(zip(dums, s_fields)))
    # XXX end of workaround
    christoffel = [[[Add(*[matrix[i, l]*ch_1st[l, j, k] for l in indices])
                     for k in indices]
                    for j in indices]
                   for i in indices]
    return ImmutableDenseNDimArray(christoffel)


def metric_to_Riemann_components(expr):
    """Return the components of the Riemann tensor expressed in a given basis.

    Given a metric it calculates the components of the Riemann tensor in the
    canonical basis of the coordinate system in which the metric expression is
    given.

    Examples
    ========

    >>> from sympy import exp
    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import metric_to_Riemann_components, TensorProduct
    >>> TP = TensorProduct
    >>> metric_to_Riemann_components(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[[[0, 0], [0, 0]], [[0, 0], [0, 0]]], [[[0, 0], [0, 0]], [[0, 0], [0, 0]]]]

    >>> non_trivial_metric = exp(2*R2.r)*TP(R2.dr, R2.dr) + \
        R2.r**2*TP(R2.dtheta, R2.dtheta)
    >>> non_trivial_metric
    r**2*TensorProduct(dtheta, dtheta) + exp(2*r)*TensorProduct(dr, dr)
    >>> riemann = metric_to_Riemann_components(non_trivial_metric)
    >>> riemann[0, :, :, :]
    [[[0, 0], [0, 0]], [[0, r*exp(-2*r)], [-r*exp(-2*r), 0]]]
    >>> riemann[1, :, :, :]
    [[[0, -1/r], [1/r, 0]], [[0, 0], [0, 0]]]

    """
    ch_2nd = metric_to_Christoffel_2nd(expr)
    coord_sys = expr.atoms(CoordSystem).pop()
    indices = list(range(coord_sys.dim))
    deriv_ch = [[[[d(ch_2nd[i, j, k])
                   for d in coord_sys.base_vectors()]
                  for k in indices]
                 for j in indices]
                for i in indices]
    riemann_a = [[[[deriv_ch[rho][sig][nu][mu] - deriv_ch[rho][sig][mu][nu]
                    for nu in indices]
                   for mu in indices]
                  for sig in indices]
                     for rho in indices]
    riemann_b = [[[[Add(*[ch_2nd[rho, l, mu]*ch_2nd[l, sig, nu] - ch_2nd[rho, l, nu]*ch_2nd[l, sig, mu] for l in indices])
                    for nu in indices]
                   for mu in indices]
                  for sig in indices]
                 for rho in indices]
    riemann = [[[[riemann_a[rho][sig][mu][nu] + riemann_b[rho][sig][mu][nu]
                  for nu in indices]
                     for mu in indices]
                for sig in indices]
               for rho in indices]
    return ImmutableDenseNDimArray(riemann)


def metric_to_Ricci_components(expr):
    """Return the components of the Ricci tensor expressed in a given basis.

    Given a metric it calculates the components of the Ricci tensor in the
    canonical basis of the coordinate system in which the metric expression is
    given.

    Examples
    ========

    >>> from sympy import exp
    >>> from sympy.diffgeom.rn import R2
    >>> from sympy.diffgeom import metric_to_Ricci_components, TensorProduct
    >>> TP = TensorProduct
    >>> metric_to_Ricci_components(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    [[0, 0], [0, 0]]

    >>> non_trivial_metric = exp(2*R2.r)*TP(R2.dr, R2.dr) + \
                             R2.r**2*TP(R2.dtheta, R2.dtheta)
    >>> non_trivial_metric
    r**2*TensorProduct(dtheta, dtheta) + exp(2*r)*TensorProduct(dr, dr)
    >>> metric_to_Ricci_components(non_trivial_metric)
    [[1/r, 0], [0, r*exp(-2*r)]]

    """
    riemann = metric_to_Riemann_components(expr)
    coord_sys = expr.atoms(CoordSystem).pop()
    indices = list(range(coord_sys.dim))
    ricci = [[Add(*[riemann[k, i, k, j] for k in indices])
              for j in indices]
             for i in indices]
    return ImmutableDenseNDimArray(ricci)
