from __future__ import unicode_literals

from graphql.language.ast import (
    BooleanValue,
    FloatValue,
    IntValue,
    ListValue,
    ObjectValue,
    StringValue,
)

from graphene.types.scalars import MAX_INT, MIN_INT

from .scalars import Scalar


class GenericScalar(Scalar):
    """
    The `GenericScalar` scalar type represents a generic
    GraphQL scalar value that could be:
    String, Boolean, Int, Float, List or Object.
    """

    @staticmethod
    def identity(value):
        return value

    serialize = identity
    parse_value = identity

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, (StringValue, BooleanValue)):
            return ast.value
        elif isinstance(ast, IntValue):
            num = int(ast.value)
            if MIN_INT <= num <= MAX_INT:
                return num
        elif isinstance(ast, FloatValue):
            return float(ast.value)
        elif isinstance(ast, ListValue):
            return [GenericScalar.parse_literal(value) for value in ast.values]
        elif isinstance(ast, ObjectValue):
            return {
                field.name.value: GenericScalar.parse_literal(field.value)
                for field in ast.fields
            }
        else:
            return None
