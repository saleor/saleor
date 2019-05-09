"""
   isort:skip_file
"""
# type: ignore
# flake8: noqa

import pytest

gevent = pytest.importorskip("gevent")

from graphql.error import format_error
from graphql.execution import execute
from graphql.language.location import SourceLocation
from graphql.language.parser import parse
from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

from ..executors.gevent import GeventExecutor
from .test_mutations import assert_evaluate_mutations_serially


def test_gevent_executor():
    def resolver(context, *_):
        gevent.sleep(0.001)
        return "hey"

    def resolver_2(context, *_):
        gevent.sleep(0.003)
        return "hey2"

    def resolver_3(contest, *_):
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
    result = execute(GraphQLSchema(Type), ast, executor=GeventExecutor())
    assert not result.errors
    assert result.data == {"a": "hey", "b": "hey2", "c": "hey3"}


def test_gevent_executor_with_error():
    ast = parse("query Example { a, b }")

    def resolver(context, *_):
        gevent.sleep(0.001)
        return "hey"

    def resolver_2(context, *_):
        gevent.sleep(0.003)
        raise Exception("resolver_2 failed!")

    Type = GraphQLObjectType(
        "Type",
        {
            "a": GraphQLField(GraphQLString, resolver=resolver),
            "b": GraphQLField(GraphQLString, resolver=resolver_2),
        },
    )

    result = execute(GraphQLSchema(Type), ast, executor=GeventExecutor())
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
    assert_evaluate_mutations_serially(executor=GeventExecutor())
