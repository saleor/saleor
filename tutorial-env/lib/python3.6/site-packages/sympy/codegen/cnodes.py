"""
AST nodes specific to the C family of languages
"""

from sympy.codegen.ast import Attribute, Declaration, Node, String, Token, Type, none, FunctionCall
from sympy.core.basic import Basic
from sympy.core.compatibility import string_types
from sympy.core.containers import Tuple
from sympy.core.sympify import sympify

void = Type('void')

restrict = Attribute('restrict')  # guarantees no pointer aliasing
volatile = Attribute('volatile')
static = Attribute('static')


def alignof(arg):
    """ Generate of FunctionCall instance for calling 'alignof' """
    return FunctionCall('alignof', [String(arg) if isinstance(arg, string_types) else arg])


def sizeof(arg):
    """ Generate of FunctionCall instance for calling 'sizeof'

    Examples
    ========

    >>> from sympy.codegen.ast import real
    >>> from sympy.codegen.cnodes import sizeof
    >>> from sympy.printing.ccode import ccode
    >>> ccode(sizeof(real))
    'sizeof(double)'
    """
    return FunctionCall('sizeof', [String(arg) if isinstance(arg, string_types) else arg])


class CommaOperator(Basic):
    """ Represents the comma operator in C """
    def __new__(cls, *args):
        return Basic.__new__(cls, *[sympify(arg) for arg in args])


class Label(String):
    """ Label for use with e.g. goto statement.

    Examples
    ========

    >>> from sympy.codegen.cnodes import Label
    >>> from sympy.printing.ccode import ccode
    >>> print(ccode(Label('foo')))
    foo:

    """

class goto(Token):
    """ Represents goto in C """
    __slots__ = ['label']
    _construct_label = Label


class PreDecrement(Basic):
    """ Represents the pre-decrement operator

    Examples
    ========

    >>> from sympy.abc import x
    >>> from sympy.codegen.cnodes import PreDecrement
    >>> from sympy.printing.ccode import ccode
    >>> ccode(PreDecrement(x))
    '--(x)'

    """
    nargs = 1


class PostDecrement(Basic):
    """ Represents the post-decrement operator """
    nargs = 1


class PreIncrement(Basic):
    """ Represents the pre-increment operator """
    nargs = 1


class PostIncrement(Basic):
    """ Represents the post-increment operator """
    nargs = 1


class struct(Node):
    """ Represents a struct in C """
    __slots__ = ['name', 'declarations']
    defaults = {'name': none}
    _construct_name = String

    @classmethod
    def _construct_declarations(cls, args):
        return Tuple(*[Declaration(arg) for arg in args])


class union(struct):
    """ Represents a union in C """
