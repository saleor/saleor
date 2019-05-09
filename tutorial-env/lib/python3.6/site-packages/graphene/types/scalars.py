import six
from graphql.language.ast import BooleanValue, FloatValue, IntValue, StringValue

from .base import BaseOptions, BaseType
from .unmountedtype import UnmountedType


class ScalarOptions(BaseOptions):
    pass


class Scalar(UnmountedType, BaseType):
    """
    Scalar Type Definition

    The leaf values of any request and input values to arguments are
    Scalars (or Enums) and are defined with a name and a series of functions
    used to parse input from ast or variables and to ensure validity.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, **options):
        _meta = ScalarOptions(cls)
        super(Scalar, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    serialize = None
    parse_value = None
    parse_literal = None

    @classmethod
    def get_type(cls):
        """
        This function is called when the unmounted type (Scalar instance)
        is mounted (as a Field, InputField or Argument)
        """
        return cls


# As per the GraphQL Spec, Integers are only treated as valid when a valid
# 32-bit signed integer, providing the broadest support across platforms.
#
# n.b. JavaScript's integers are safe between -(2^53 - 1) and 2^53 - 1 because
# they are internally represented as IEEE 754 doubles.
MAX_INT = 2147483647
MIN_INT = -2147483648


class Int(Scalar):
    """
    The `Int` scalar type represents non-fractional signed whole numeric
    values. Int can represent values between -(2^53 - 1) and 2^53 - 1 since
    represented in JSON as double-precision floating point numbers specified
    by [IEEE 754](http://en.wikipedia.org/wiki/IEEE_floating_point).
    """

    @staticmethod
    def coerce_int(value):
        try:
            num = int(value)
        except ValueError:
            try:
                num = int(float(value))
            except ValueError:
                return None
        if MIN_INT <= num <= MAX_INT:
            return num

    serialize = coerce_int
    parse_value = coerce_int

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, IntValue):
            num = int(ast.value)
            if MIN_INT <= num <= MAX_INT:
                return num


class Float(Scalar):
    """
    The `Float` scalar type represents signed double-precision fractional
    values as specified by
    [IEEE 754](http://en.wikipedia.org/wiki/IEEE_floating_point).
    """

    @staticmethod
    def coerce_float(value):
        # type: (Any) -> float
        try:
            return float(value)
        except ValueError:
            return None

    serialize = coerce_float
    parse_value = coerce_float

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, (FloatValue, IntValue)):
            return float(ast.value)


class String(Scalar):
    """
    The `String` scalar type represents textual data, represented as UTF-8
    character sequences. The String type is most often used by GraphQL to
    represent free-form human-readable text.
    """

    @staticmethod
    def coerce_string(value):
        if isinstance(value, bool):
            return u"true" if value else u"false"
        return six.text_type(value)

    serialize = coerce_string
    parse_value = coerce_string

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, StringValue):
            return ast.value


class Boolean(Scalar):
    """
    The `Boolean` scalar type represents `true` or `false`.
    """

    serialize = bool
    parse_value = bool

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, BooleanValue):
            return ast.value


class ID(Scalar):
    """
    The `ID` scalar type represents a unique identifier, often used to
    refetch an object or as key for a cache. The ID type appears in a JSON
    response as a String; however, it is not intended to be human-readable.
    When expected as an input type, any string (such as `"4"`) or integer
    (such as `4`) input value will be accepted as an ID.
    """

    serialize = str
    parse_value = str

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, (StringValue, IntValue)):
            return ast.value
