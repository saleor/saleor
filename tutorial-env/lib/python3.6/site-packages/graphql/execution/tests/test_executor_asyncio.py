"""
   isort:skip_file
"""
# type: ignore
# flake8: noqa

import pytest

asyncio = pytest.importorskip("asyncio")

from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

from ..executors.asyncio import AsyncioExecutor
from .test_mutations import assert_evaluate_mutations_serially


def test_asyncio_executor():
    # type: () -> None
    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        asyncio.sleep(0.001)
        return "hey"

    @asyncio.coroutine
    def resolver_2(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        asyncio.sleep(0.003)
        return "hey2"

    def resolver_3(contest, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        return "hey3"

    Type = GraphQLObjectType(
        "Type",
        {
            "a": GraphQLField(GraphQLString, resolver=resolver),
            "b": GraphQLField(GraphQLString, resolver=resolver_2),
            "c": GraphQLField(GraphQLString, resolver=resolver_3),
        },
    )

    ast = parse("{ a b c }")
    result = execute(GraphQLSchema(Type), ast, executor=AsyncioExecutor())
    assert not result.errors
    assert result.data == {"a": "hey", "b": "hey2", "c": "hey3"}


def test_asyncio_executor_custom_loop():
    # type: () -> None
    loop = asyncio.get_event_loop()

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        asyncio.sleep(0.001, loop=loop)
        return "hey"

    @asyncio.coroutine
    def resolver_2(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        asyncio.sleep(0.003, loop=loop)
        return "hey2"

    def resolver_3(contest, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        return "hey3"

    Type = GraphQLObjectType(
        "Type",
        {
            "a": GraphQLField(GraphQLString, resolver=resolver),
            "b": GraphQLField(GraphQLString, resolver=resolver_2),
            "c": GraphQLField(GraphQLString, resolver=resolver_3),
        },
    )

    ast = parse("{ a b c }")
    result = execute(GraphQLSchema(Type), ast, executor=AsyncioExecutor(loop=loop))
    assert not result.errors
    assert result.data == {"a": "hey", "b": "hey2", "c": "hey3"}


def test_asyncio_executor_with_error():
    # type: () -> None
    ast = parse("query Example { a, b }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> str
        asyncio.sleep(0.001)
        return "hey"

    def resolver_2(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> NoReturn
        asyncio.sleep(0.003)
        raise Exception("resolver_2 failed!")

    Type = GraphQLObjectType(
        "Type",
        {
            "a": GraphQLField(GraphQLString, resolver=resolver),
            "b": GraphQLField(GraphQLString, resolver=resolver_2),
        },
    )

    result = execute(GraphQLSchema(Type), ast, executor=AsyncioExecutor())
    formatted_errors = list(map(format_error, result.errors))
    assert formatted_errors == [
        {
            "locations": [{"line": 1, "column": 20}],
            "path": ["b"],
            "message": "resolver_2 failed!",
        }
    ]
    assert result.data == {"a": "hey", "b": None}


def test_evaluates_mutations_serially():
    # type: () -> None
    assert_evaluate_mutations_serially(executor=AsyncioExecutor())
