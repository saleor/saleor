import pytest
import traceback

from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

# Necessary for static type checking
if False:  # flake8: noqa
    from graphql.execution.base import ResolveInfo
    from typing import Any
    from typing import Optional


def test_raise():
    # type: () -> None
    ast = parse("query Example { a }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> None
        raise Exception("Failed")

    Type = GraphQLObjectType(
        "Type", {"a": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    assert str(result.errors[0]) == "Failed"


def test_reraise():
    # type: () -> None
    ast = parse("query Example { a }")

    def resolver(context, *_):
        # type: (Optional[Any], *ResolveInfo) -> None
        raise Exception("Failed")

    Type = GraphQLObjectType(
        "Type", {"a": GraphQLField(GraphQLString, resolver=resolver)}
    )

    result = execute(GraphQLSchema(Type), ast)
    with pytest.raises(Exception) as exc_info:
        result.errors[0].reraise()

    extracted = traceback.extract_tb(exc_info.tb)
    formatted_tb = [row[2:] for row in extracted]
    if formatted_tb[2][0] == "reraise":
        formatted_tb[2:] = formatted_tb[3:]

    assert formatted_tb == [
        ("test_reraise", "result.errors[0].reraise()"),
        ("reraise", "six.reraise(type(self), self, self.stack)"),
        # ('reraise', 'raise value.with_traceback(tb)'),
        (
            "resolve_or_error",
            "return executor.execute(resolve_fn, source, info, **args)",
        ),
        ("execute", "return fn(*args, **kwargs)"),
        ("resolver", 'raise Exception("Failed")'),
    ]
    # assert formatted_tb == [
    #     ('test_reraise', 'result.errors[0].reraise()'),
    #     ('reraise', 'six.reraise(type(self), self, self.stack)'),
    #     ('on_complete_resolver', 'result = __resolver(*args, **kwargs)'),
    #     # ('reraise', 'raise value.with_traceback(tb)'),
    #     # ('resolve_or_error', 'return executor.execute(resolve_fn, source, info, **args)'),
    #     # ('execute', 'return fn(*args, **kwargs)'),
    #     ('resolver', "raise Exception('Failed')")
    # ]

    assert str(exc_info.value) == "Failed"
