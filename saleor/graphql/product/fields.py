from json import JSONDecodeError

import graphene
from graphql.error import GraphQLError


class JSONStringWithValidation(graphene.JSONString):
    @staticmethod
    def parse_literal(node):
        try:
            graphene.JSONString.parse_literal(node)
        except JSONDecodeError:
            raise GraphQLError(f"{str(node.value)[:20]}... is not a valid JSONString")
