""" The core's core. """
from __future__ import print_function, division

# used for canonical ordering of symbolic sequences
# via __cmp__ method:
# FIXME this is *so* irrelevant and outdated!
ordering_of_classes = [
    # singleton numbers
    'Zero', 'One', 'Half', 'Infinity', 'NaN', 'NegativeOne', 'NegativeInfinity',
    # numbers
    'Integer', 'Rational', 'Float',
    # singleton symbols
    'Exp1', 'Pi', 'ImaginaryUnit',
    # symbols
    'Symbol', 'Wild', 'Temporary',
    # arithmetic operations
    'Pow', 'Mul', 'Add',
    # function values
    'Derivative', 'Integral',
    # defined singleton functions
    'Abs', 'Sign', 'Sqrt',
    'Floor', 'Ceiling',
    'Re', 'Im', 'Arg',
    'Conjugate',
    'Exp', 'Log',
    'Sin', 'Cos', 'Tan', 'Cot', 'ASin', 'ACos', 'ATan', 'ACot',
    'Sinh', 'Cosh', 'Tanh', 'Coth', 'ASinh', 'ACosh', 'ATanh', 'ACoth',
    'RisingFactorial', 'FallingFactorial',
    'factorial', 'binomial',
    'Gamma', 'LowerGamma', 'UpperGamma', 'PolyGamma',
    'Erf',
    # special polynomials
    'Chebyshev', 'Chebyshev2',
    # undefined functions
    'Function', 'WildFunction',
    # anonymous functions
    'Lambda',
    # Landau O symbol
    'Order',
    # relational operations
    'Equality', 'Unequality', 'StrictGreaterThan', 'StrictLessThan',
    'GreaterThan', 'LessThan',
]


class Registry(object):
    """
    Base class for registry objects.

    Registries map a name to an object using attribute notation. Registry
    classes behave singletonically: all their instances share the same state,
    which is stored in the class object.

    All subclasses should set `__slots__ = []`.
    """
    __slots__ = []

    def __setattr__(self, name, obj):
        setattr(self.__class__, name, obj)

    def __delattr__(self, name):
        delattr(self.__class__, name)

#A set containing all sympy class objects
all_classes = set()


class BasicMeta(type):

    def __init__(cls, *args, **kws):
        all_classes.add(cls)

    def __cmp__(cls, other):
        # If the other object is not a Basic subclass, then we are not equal to
        # it.
        if not isinstance(other, BasicMeta):
            return -1
        n1 = cls.__name__
        n2 = other.__name__
        if n1 == n2:
            return 0

        UNKNOWN = len(ordering_of_classes) + 1
        try:
            i1 = ordering_of_classes.index(n1)
        except ValueError:
            i1 = UNKNOWN
        try:
            i2 = ordering_of_classes.index(n2)
        except ValueError:
            i2 = UNKNOWN
        if i1 == UNKNOWN and i2 == UNKNOWN:
            return (n1 > n2) - (n1 < n2)
        return (i1 > i2) - (i1 < i2)

    def __lt__(cls, other):
        if cls.__cmp__(other) == -1:
            return True
        return False

    def __gt__(cls, other):
        if cls.__cmp__(other) == 1:
            return True
        return False
