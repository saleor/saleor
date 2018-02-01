from graphene.types import Scalar
from graphql.language import ast


class AttributesFilterScalar(Scalar):

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            splitted = node.value.split(":")
            if len(splitted) == 2:
                return tuple(splitted)
        return None

    @staticmethod
    def parse_value(value):
        if isinstance(value, str):
            splitted = value.split(":")
            if len(splitted) == 2:
                return tuple(splitted)
        return None

    @staticmethod
    def serialize(value):
        if isinstance(value, tuple) and len(value) == 2:
            return ":".join(value)
        return None
