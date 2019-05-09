# type: ignore
# coding: utf-8

from graphql import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    execute,
    parse,
)
from graphql.error import GraphQLLocatedError


def test_unicode_error_message():
    # type: () -> None
    ast = parse("query Example { unicode }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> NoReturn
        raise Exception(u"UNIÇODÉ!")

    Type = GraphQLObjectType(
        "Type", {"unicode": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    assert isinstance(result.errors[0], GraphQLLocatedError)
