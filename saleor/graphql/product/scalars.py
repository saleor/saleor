from graphene.types import Scalar
from graphql.language import ast


class AttributeScalar(Scalar):
    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            split = node.value.split(':')
            if len(split) == 2:
                return tuple(split)
        return None

    @staticmethod
    def parse_value(value):
        if isinstance(value, str):
            split = value.split(':')
            if len(split) == 2:
                return tuple(split)
        return None

    @staticmethod
    def serialize(value):
        if isinstance(value, tuple) and len(value) == 2:
            return ':'.join(value)
        return None
