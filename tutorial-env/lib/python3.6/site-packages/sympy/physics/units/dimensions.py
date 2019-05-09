# -*- coding:utf-8 -*-

"""
Definition of physical dimensions.

Unit systems will be constructed on top of these dimensions.

Most of the examples in the doc use MKS system and are presented from the
computer point of view: from a human point, adding length to time is not legal
in MKS but it is in natural system; for a computer in natural system there is
no time dimension (but a velocity dimension instead) - in the basis - so the
question of adding time to length has no meaning.
"""

from __future__ import division

import collections

from sympy import Integer, Matrix, S, Symbol, sympify, Basic, Tuple, Dict, default_sort_key
from sympy.core.compatibility import reduce, string_types
from sympy.core.basic import Basic
from sympy.core.expr import Expr
from sympy.core.power import Pow
from sympy.utilities.exceptions import SymPyDeprecationWarning


class Dimension(Expr):
    """
    This class represent the dimension of a physical quantities.

    The ``Dimension`` constructor takes as parameters a name and an optional
    symbol.

    For example, in classical mechanics we know that time is different from
    temperature and dimensions make this difference (but they do not provide
    any measure of these quantites.

        >>> from sympy.physics.units import Dimension
        >>> length = Dimension('length')
        >>> length
        Dimension(length)
        >>> time = Dimension('time')
        >>> time
        Dimension(time)

    Dimensions can be composed using multiplication, division and
    exponentiation (by a number) to give new dimensions. Addition and
    subtraction is defined only when the two objects are the same dimension.

        >>> velocity = length / time
        >>> velocity
        Dimension(length/time)

    It is possible to use a dimension system object to get the dimensionsal
    dependencies of a dimension, for example the dimension system used by the
    SI units convention can be used:

        >>> from sympy.physics.units.dimensions import dimsys_SI
        >>> dimsys_SI.get_dimensional_dependencies(velocity)
        {'length': 1, 'time': -1}
        >>> length + length
        Dimension(length)
        >>> l2 = length**2
        >>> l2
        Dimension(length**2)
        >>> dimsys_SI.get_dimensional_dependencies(l2)
        {'length': 2}

    """

    _op_priority = 13.0

    _dimensional_dependencies = dict()

    is_commutative = True
    is_number = False
    # make sqrt(M**2) --> M
    is_positive = True
    is_real = True

    def __new__(cls, name, symbol=None):

        if isinstance(name, string_types):
            name = Symbol(name)
        else:
            name = sympify(name)

        if not isinstance(name, Expr):
            raise TypeError("Dimension name needs to be a valid math expression")

        if isinstance(symbol, string_types):
            symbol = Symbol(symbol)
        elif symbol is not None:
            assert isinstance(symbol, Symbol)

        if symbol is not None:
            obj = Expr.__new__(cls, name, symbol)
        else:
            obj = Expr.__new__(cls, name)

        obj._name = name
        obj._symbol = symbol
        return obj

    @property
    def name(self):
        return self._name

    @property
    def symbol(self):
        return self._symbol

    def __hash__(self):
        return Expr.__hash__(self)

    def __eq__(self, other):
        if isinstance(other, Dimension):
            return self.name == other.name
        return False

    def __str__(self):
        """
        Display the string representation of the dimension.
        """
        if self.symbol is None:
            return "Dimension(%s)" % (self.name)
        else:
            return "Dimension(%s, %s)" % (self.name, self.symbol)

    def __repr__(self):
        return self.__str__()

    def __neg__(self):
        return self

    def _register_as_base_dim(self):
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="do not call ._register_as_base_dim()",
            useinstead="DimensionSystem"
        ).warn()
        if not self.name.is_Symbol:
            raise TypeError("Base dimensions need to have symbolic name")

        name = self.name
        if name in dimsys_default.dimensional_dependencies:
            raise IndexError("already in dependencies dict")
        # Horrible code:
        d = dict(dimsys_default.dimensional_dependencies)
        d[name] = Dict({name: 1})
        dimsys_default._args = (dimsys_default.args[:2] + (Dict(d),))

    def __add__(self, other):
        from sympy.physics.units.quantities import Quantity
        other = sympify(other)
        if isinstance(other, Basic):
            if other.has(Quantity):
                other = Dimension(Quantity.get_dimensional_expr(other))
            if isinstance(other, Dimension) and self == other:
                return self
            return super(Dimension, self).__add__(other)
        return self

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        # there is no notion of ordering (or magnitude) among dimension,
        # subtraction is equivalent to addition when the operation is legal
        return self + other

    def __rsub__(self, other):
        # there is no notion of ordering (or magnitude) among dimension,
        # subtraction is equivalent to addition when the operation is legal
        return self + other

    def __pow__(self, other):
        return self._eval_power(other)

    def _eval_power(self, other):
        other = sympify(other)
        return Dimension(self.name**other)

    def __mul__(self, other):
        from sympy.physics.units.quantities import Quantity
        if isinstance(other, Basic):
            if other.has(Quantity):
                other = Dimension(Quantity.get_dimensional_expr(other))
            if isinstance(other, Dimension):
                return Dimension(self.name*other.name)
            if not other.free_symbols: # other.is_number cannot be used
                return self
            return super(Dimension, self).__mul__(other)
        return self

    def __rmul__(self, other):
        return self*other

    def __div__(self, other):
        return self*Pow(other, -1)

    def __rdiv__(self, other):
        return other * pow(self, -1)

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def get_dimensional_dependencies(self, mark_dimensionless=False):
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="do not call",
            useinstead="DimensionSystem"
        ).warn()
        name = self.name
        dimdep = dimsys_default.get_dimensional_dependencies(name)
        if mark_dimensionless and dimdep == {}:
            return {'dimensionless': 1}
        return {str(i): j for i, j in dimdep.items()}

    @classmethod
    def _from_dimensional_dependencies(cls, dependencies):
        return reduce(lambda x, y: x * y, (
            Dimension(d)**e for d, e in dependencies.items()
        ))

    @classmethod
    def _get_dimensional_dependencies_for_name(cls, name):
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="do not call from `Dimension` objects.",
            useinstead="DimensionSystem"
        ).warn()
        return dimsys_default.get_dimensional_dependencies(name)

    @property
    def is_dimensionless(self, dimensional_dependencies=None):
        """
        Check if the dimension object really has a dimension.

        A dimension should have at least one component with non-zero power.
        """
        if self.name == 1:
            return True
        if dimensional_dependencies is None:
            SymPyDeprecationWarning(
                deprecated_since_version="1.2",
                issue=13336,
                feature="wrong class",
            ).warn()
            dimensional_dependencies=dimsys_default
        return dimensional_dependencies.get_dimensional_dependencies(self) == {}

    def has_integer_powers(self, dim_sys):
        """
        Check if the dimension object has only integer powers.

        All the dimension powers should be integers, but rational powers may
        appear in intermediate steps. This method may be used to check that the
        final result is well-defined.
        """

        for dpow in dim_sys.get_dimensional_dependencies(self).values():
            if not isinstance(dpow, (int, Integer)):
                return False
        else:
            return True


# base dimensions (MKS)
length = Dimension(name="length", symbol="L")
mass = Dimension(name="mass", symbol="M")
time = Dimension(name="time", symbol="T")

# base dimensions (MKSA not in MKS)
current = Dimension(name='current', symbol='I')

# other base dimensions:
temperature = Dimension("temperature", "T")
amount_of_substance = Dimension("amount_of_substance")
luminous_intensity = Dimension("luminous_intensity")

# derived dimensions (MKS)
velocity = Dimension(name="velocity")
acceleration = Dimension(name="acceleration")
momentum = Dimension(name="momentum")
force = Dimension(name="force", symbol="F")
energy = Dimension(name="energy", symbol="E")
power = Dimension(name="power")
pressure = Dimension(name="pressure")
frequency = Dimension(name="frequency", symbol="f")
action = Dimension(name="action", symbol="A")
volume = Dimension("volume")

# derived dimensions (MKSA not in MKS)
voltage = Dimension(name='voltage', symbol='U')
impedance = Dimension(name='impedance', symbol='Z')
conductance = Dimension(name='conductance', symbol='G')
capacitance = Dimension(name='capacitance')
inductance = Dimension(name='inductance')
charge = Dimension(name='charge', symbol='Q')
magnetic_density = Dimension(name='magnetic_density', symbol='B')
magnetic_flux = Dimension(name='magnetic_flux')

# Dimensions in information theory:
information = Dimension(name='information')

# Create dimensions according the the base units in MKSA.
# For other unit systems, they can be derived by transforming the base
# dimensional dependency dictionary.


class DimensionSystem(Basic):
    r"""
    DimensionSystem represents a coherent set of dimensions.

    The constructor takes three parameters:

    - base dimensions;
    - derived dimensions: these are defined in terms of the base dimensions
      (for example velocity is defined from the division of length by time);
    - dependency of dimensions: how the derived dimensions depend
      on the base dimensions.

    Optionally either the ``derived_dims`` or the ``dimensional_dependencies``
    may be omitted.
    """

    def __new__(cls, base_dims, derived_dims=[], dimensional_dependencies={}, name=None, descr=None):
        dimensional_dependencies = dict(dimensional_dependencies)

        if (name is not None) or (descr is not None):
            SymPyDeprecationWarning(
                deprecated_since_version="1.2",
                issue=13336,
                useinstead="do not define a `name` or `descr`",
            ).warn()

        def parse_dim(dim):
            if isinstance(dim, string_types):
                dim = Dimension(Symbol(dim))
            elif isinstance(dim, Dimension):
                pass
            elif isinstance(dim, Symbol):
                dim = Dimension(dim)
            else:
                raise TypeError("%s wrong type" % dim)
            return dim

        base_dims = [parse_dim(i) for i in base_dims]
        derived_dims = [parse_dim(i) for i in derived_dims]

        for dim in base_dims:
            dim = dim.name
            if (dim in dimensional_dependencies
                and (len(dimensional_dependencies[dim]) != 1 or
                dimensional_dependencies[dim].get(dim, None) != 1)):
                raise IndexError("Repeated value in base dimensions")
            dimensional_dependencies[dim] = Dict({dim: 1})

        def parse_dim_name(dim):
            if isinstance(dim, Dimension):
                return dim.name
            elif isinstance(dim, string_types):
                return Symbol(dim)
            elif isinstance(dim, Symbol):
                return dim
            else:
                raise TypeError("unrecognized type %s for %s" % (type(dim), dim))

        for dim in dimensional_dependencies.keys():
            dim = parse_dim(dim)
            if (dim not in derived_dims) and (dim not in base_dims):
                derived_dims.append(dim)

        def parse_dict(d):
            return Dict({parse_dim_name(i): j for i, j in d.items()})

        # Make sure everything is a SymPy type:
        dimensional_dependencies = {parse_dim_name(i): parse_dict(j) for i, j in
                                    dimensional_dependencies.items()}

        for dim in derived_dims:
            if dim in base_dims:
                raise ValueError("Dimension %s both in base and derived" % dim)
            if dim.name not in dimensional_dependencies:
                # TODO: should this raise a warning?
                dimensional_dependencies[dim] = Dict({dim.name: 1})

        base_dims.sort(key=default_sort_key)
        derived_dims.sort(key=default_sort_key)

        base_dims = Tuple(*base_dims)
        derived_dims = Tuple(*derived_dims)
        dimensional_dependencies = Dict({i: Dict(j) for i, j in dimensional_dependencies.items()})
        obj = Basic.__new__(cls, base_dims, derived_dims, dimensional_dependencies)
        return obj

    @property
    def base_dims(self):
        return self.args[0]

    @property
    def derived_dims(self):
        return self.args[1]

    @property
    def dimensional_dependencies(self):
        return self.args[2]

    def _get_dimensional_dependencies_for_name(self, name):

        if name.is_Symbol:
            return dict(self.dimensional_dependencies.get(name, {}))

        if name.is_Number:
            return {}

        get_for_name = dimsys_default._get_dimensional_dependencies_for_name

        if name.is_Mul:
            ret = collections.defaultdict(int)
            dicts = [get_for_name(i) for i in name.args]
            for d in dicts:
                for k, v in d.items():
                    ret[k] += v
            return {k: v for (k, v) in ret.items() if v != 0}

        if name.is_Pow:
            dim = get_for_name(name.base)
            return {k: v*name.exp for (k, v) in dim.items()}

        if name.is_Function:
            args = (Dimension._from_dimensional_dependencies(
                get_for_name(arg)) for arg in name.args)
            result = name.func(*args)

            if isinstance(result, Dimension):
                return dimsys_default.get_dimensional_dependencies(result)
            elif result.func == name.func:
                return {}
            else:
                return get_for_name(result)

    def get_dimensional_dependencies(self, name, mark_dimensionless=False):
        if isinstance(name, Dimension):
            name = name.name
        if isinstance(name, string_types):
            name = Symbol(name)

        dimdep = self._get_dimensional_dependencies_for_name(name)
        if mark_dimensionless and dimdep == {}:
            return {'dimensionless': 1}
        return {str(i): j for i, j in dimdep.items()}

    def equivalent_dims(self, dim1, dim2):
        deps1 = self.get_dimensional_dependencies(dim1)
        deps2 = self.get_dimensional_dependencies(dim2)
        return deps1 == deps2

    def extend(self, new_base_dims, new_derived_dims=[], new_dim_deps={}, name=None, description=None):
        if (name is not None) or (description is not None):
            SymPyDeprecationWarning(
                deprecated_since_version="1.2",
                issue=13336,
                feature="name and descriptions of DimensionSystem",
                useinstead="do not specify `name` or `description`",
            ).warn()

        deps = dict(self.dimensional_dependencies)
        deps.update(new_dim_deps)

        return DimensionSystem(
            tuple(self.base_dims) + tuple(new_base_dims),
            tuple(self.derived_dims) + tuple(new_derived_dims),
            deps
        )

    @staticmethod
    def sort_dims(dims):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Sort dimensions given in argument using their str function.

        This function will ensure that we get always the same tuple for a given
        set of dimensions.
        """
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="sort_dims",
            useinstead="sorted(..., key=default_sort_key)",
        ).warn()
        return tuple(sorted(dims, key=str))

    def __getitem__(self, key):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Shortcut to the get_dim method, using key access.
        """
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="the get [ ] operator",
            useinstead="the dimension definition",
        ).warn()
        d = self.get_dim(key)
        #TODO: really want to raise an error?
        if d is None:
            raise KeyError(key)
        return d

    def __call__(self, unit):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Wrapper to the method print_dim_base
        """
        SymPyDeprecationWarning(
            deprecated_since_version="1.2",
            issue=13336,
            feature="call DimensionSystem",
            useinstead="the dimension definition",
        ).warn()
        return self.print_dim_base(unit)

    def is_dimensionless(self, dimension):
        """
        Check if the dimension object really has a dimension.

        A dimension should have at least one component with non-zero power.
        """
        if dimension.name == 1:
            return True
        return self.get_dimensional_dependencies(dimension) == {}

    @property
    def list_can_dims(self):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        List all canonical dimension names.
        """
        dimset = set([])
        for i in self.base_dims:
            dimset.update(set(dimsys_default.get_dimensional_dependencies(i).keys()))
        return tuple(sorted(dimset, key=str))

    @property
    def inv_can_transf_matrix(self):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Compute the inverse transformation matrix from the base to the
        canonical dimension basis.

        It corresponds to the matrix where columns are the vector of base
        dimensions in canonical basis.

        This matrix will almost never be used because dimensions are always
        defined with respect to the canonical basis, so no work has to be done
        to get them in this basis. Nonetheless if this matrix is not square
        (or not invertible) it means that we have chosen a bad basis.
        """
        matrix = reduce(lambda x, y: x.row_join(y),
                        [self.dim_can_vector(d) for d in self.base_dims])
        return matrix

    @property
    def can_transf_matrix(self):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Return the canonical transformation matrix from the canonical to the
        base dimension basis.

        It is the inverse of the matrix computed with inv_can_transf_matrix().
        """

        #TODO: the inversion will fail if the system is inconsistent, for
        #      example if the matrix is not a square
        return reduce(lambda x, y: x.row_join(y),
                      [self.dim_can_vector(d) for d in sorted(self.base_dims, key=str)]
                      ).inv()

    def dim_can_vector(self, dim):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Dimensional representation in terms of the canonical base dimensions.
        """

        vec = []
        for d in self.list_can_dims:
            vec.append(dimsys_default.get_dimensional_dependencies(dim).get(d, 0))
        return Matrix(vec)

    def dim_vector(self, dim):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.


        Vector representation in terms of the base dimensions.
        """
        return self.can_transf_matrix * Matrix(self.dim_can_vector(dim))

    def print_dim_base(self, dim):
        """
        Give the string expression of a dimension in term of the basis symbols.
        """
        dims = self.dim_vector(dim)
        symbols = [i.symbol if i.symbol is not None else i.name for i in self.base_dims]
        res = S.One
        for (s, p) in zip(symbols, dims):
            res *= s**p
        return res

    @property
    def dim(self):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Give the dimension of the system.

        That is return the number of dimensions forming the basis.
        """
        return len(self.base_dims)

    @property
    def is_consistent(self):
        """
        Useless method, kept for compatibility with previous versions.

        DO NOT USE.

        Check if the system is well defined.
        """

        # not enough or too many base dimensions compared to independent
        # dimensions
        # in vector language: the set of vectors do not form a basis
        return self.inv_can_transf_matrix.is_square


dimsys_MKS = DimensionSystem([
    # Dimensional dependencies for MKS base dimensions
    length,
    mass,
    time,
], dimensional_dependencies=dict(
    # Dimensional dependencies for derived dimensions
    velocity=dict(length=1, time=-1),
    acceleration=dict(length=1, time=-2),
    momentum=dict(mass=1, length=1, time=-1),
    force=dict(mass=1, length=1, time=-2),
    energy=dict(mass=1, length=2, time=-2),
    power=dict(length=2, mass=1, time=-3),
    pressure=dict(mass=1, length=-1, time=-2),
    frequency=dict(time=-1),
    action=dict(length=2, mass=1, time=-1),
    volume=dict(length=3),
))

dimsys_MKSA = dimsys_MKS.extend([
    # Dimensional dependencies for base dimensions (MKSA not in MKS)
    current,
], new_dim_deps=dict(
    # Dimensional dependencies for derived dimensions
    voltage=dict(mass=1, length=2, current=-1, time=-3),
    impedance=dict(mass=1, length=2, current=-2, time=-3),
    conductance=dict(mass=-1, length=-2, current=2, time=3),
    capacitance=dict(mass=-1, length=-2, current=2, time=4),
    inductance=dict(mass=1, length=2, current=-2, time=-2),
    charge=dict(current=1, time=1),
    magnetic_density=dict(mass=1, current=-1, time=-2),
    magnetic_flux=dict(length=2, mass=1, current=-1, time=-2),
))

dimsys_SI = dimsys_MKSA.extend(
    [
        # Dimensional dependencies for other base dimensions:
        temperature,
        amount_of_substance,
        luminous_intensity,
    ])

dimsys_default = dimsys_SI.extend(
    [information],
)
