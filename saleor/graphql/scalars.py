from graphene.types import Scalar
from graphql.language import ast


class FilterScalar(Scalar):

    @staticmethod
    def coerce_filter(value):
        if isinstance(value, tuple) and len(value) == 2:
            return ":".join(value)

    serialize = coerce_filter
    parse_value = coerce_filter

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            splitted = node.value.split(":")
            if len(splitted) == 2:
                return tuple(splitted)
