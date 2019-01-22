from graphene.types import Scalar
from graphql.language import ast

from ...product.filters import parse_attribute, serialize_attribute


class AttributeScalar(Scalar):
    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return parse_attribute(node.value)
        return None

    @staticmethod
    def parse_value(value):
        return parse_attribute(value)

    @staticmethod
    def serialize(value):
        return serialize_attribute(value)
