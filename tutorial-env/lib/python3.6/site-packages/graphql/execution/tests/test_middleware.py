# type: ignore
from __future__ import print_function

import json

from pytest import raises
from graphql.error import GraphQLError
from graphql.execution import MiddlewareManager, execute
from graphql.execution.middleware import get_middleware_resolvers, middleware_chain
from graphql.language.parser import parse
from graphql.type import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
    GraphQLNonNull,
    GraphQLID,
)
from promise import Promise


def test_middleware():
    # type: () -> None
    doc = """{
        ok
        not_ok
    }"""

    class Data(object):
        def ok(self):
            # type: () -> str
            return "ok"

        def not_ok(self):
            # type: () -> str
            return "not_ok"

    doc_ast = parse(doc)

    Type = GraphQLObjectType(
        "Type",
        {"ok": GraphQLField(GraphQLString), "not_ok": GraphQLField(GraphQLString)},
    )

    def reversed_middleware(next, *args, **kwargs):
        # type: (Callable, *Any, **Any) -> Promise
        p = next(*args, **kwargs)
        return p.then(lambda x: x[::-1])

    middlewares = MiddlewareManager(reversed_middleware)
    result = execute(GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares)
    assert result.data == {"ok": "ko", "not_ok": "ko_ton"}


def test_middleware_class():
    # type: () -> None
    doc = """{
        ok
        not_ok
    }"""

    class Data(object):
        def ok(self):
            # type: () -> str
            return "ok"

        def not_ok(self):
            # type: () -> str
            return "not_ok"

    doc_ast = parse(doc)

    Type = GraphQLObjectType(
        "Type",
        {"ok": GraphQLField(GraphQLString), "not_ok": GraphQLField(GraphQLString)},
    )

    class MyMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            # type: (Callable, *Any, **Any) -> Promise
            p = next(*args, **kwargs)
            return p.then(lambda x: x[::-1])

    middlewares = MiddlewareManager(MyMiddleware())
    result = execute(GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares)
    assert result.data == {"ok": "ko", "not_ok": "ko_ton"}


def test_middleware_skip_promise_wrap():
    # type: () -> None
    doc = """{
        ok
        not_ok
    }"""

    class Data(object):
        def ok(self):
            # type: () -> str
            return "ok"

        def not_ok(self):
            # type: () -> str
            return "not_ok"

    doc_ast = parse(doc)

    Type = GraphQLObjectType(
        "Type",
        {"ok": GraphQLField(GraphQLString), "not_ok": GraphQLField(GraphQLString)},
    )

    class MyPromiseMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            # type: (Callable, *Any, **Any) -> Promise
            return Promise.resolve(next(*args, **kwargs))

    class MyEmptyMiddleware(object):
        def resolve(self, next, *args, **kwargs):
            # type: (Callable, *Any, **Any) -> str
            return next(*args, **kwargs)

    middlewares_with_promise = MiddlewareManager(
        MyPromiseMiddleware(), wrap_in_promise=False
    )
    middlewares_without_promise = MiddlewareManager(
        MyEmptyMiddleware(), wrap_in_promise=False
    )

    result1 = execute(
        GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares_with_promise
    )
    result2 = execute(
        GraphQLSchema(Type), doc_ast, Data(), middleware=middlewares_without_promise
    )
    assert result1.data == result2.data and result1.data == {
        "ok": "ok",
        "not_ok": "not_ok",
    }


def test_middleware_chain(capsys):
    # type: (Any) -> None
    class CharPrintingMiddleware(object):
        def __init__(self, char):
            # type: (str) -> None
            self.char = char

        def resolve(self, next, *args, **kwargs):
            # type: (Callable, *Any, **Any) -> str
            print("resolve() called for middleware {}".format(self.char))
            return next(*args, **kwargs).then(
                lambda x: print("then() for {}".format(self.char))
            )

    middlewares = [
        CharPrintingMiddleware("a"),
        CharPrintingMiddleware("b"),
        CharPrintingMiddleware("c"),
    ]

    middlewares_resolvers = get_middleware_resolvers(middlewares)

    def func():
        # type: () -> None
        return

    chain_iter = middleware_chain(func, middlewares_resolvers, wrap_in_promise=True)

    assert_stdout(capsys, "")

    chain_iter()

    expected_stdout = (
        "resolve() called for middleware c\n"
        "resolve() called for middleware b\n"
        "resolve() called for middleware a\n"
        "then() for a\n"
        "then() for b\n"
        "then() for c\n"
    )
    assert_stdout(capsys, expected_stdout)


def assert_stdout(capsys, expected_stdout):
    # type: (Any, str) -> None
    captured = capsys.readouterr()
    assert captured.out == expected_stdout
