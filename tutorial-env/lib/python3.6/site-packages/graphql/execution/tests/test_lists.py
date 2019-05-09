# type: ignore
from collections import namedtuple

from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (
    GraphQLField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
)

from .utils import rejected, resolved

Data = namedtuple("Data", "test")
ast = parse("{ nest { test } }")


def check(test_data, expected):
    def run_check(self):
        # type: (Any) -> None
        test_type = self.type

        data = Data(test=test_data)
        DataType = GraphQLObjectType(
            name="DataType",
            fields=lambda: {
                "test": GraphQLField(test_type),
                "nest": GraphQLField(DataType, resolver=lambda *_: data),
            },
        )

        schema = GraphQLSchema(query=DataType)
        response = execute(schema, ast, data)

        if response.errors:
            result = {
                "data": response.data,
                "errors": [format_error(e) for e in response.errors],
            }
        else:
            result = {"data": response.data}

        assert result == expected

    return run_check


class Test_ListOfT_Array_T:  # [T] Array<T>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check([1, 2], {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check([1, None, 2], {"data": {"nest": {"test": [1, None, 2]}}})
    test_returns_null = check(None, {"data": {"nest": {"test": None}}})


class Test_ListOfT_Promise_Array_T:  # [T] Promise<Array<T>>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check(resolved([1, 2]), {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        resolved([1, None, 2]), {"data": {"nest": {"test": [1, None, 2]}}}
    )
    test_returns_null = check(resolved(None), {"data": {"nest": {"test": None}}})
    test_rejected = check(
        lambda: rejected(Exception("bad")),
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "bad",
                }
            ],
        },
    )


class Test_ListOfT_Array_Promise_T:  # [T] Array<Promise<T>>
    type = GraphQLList(GraphQLInt)

    test_contains_values = check(
        [resolved(1), resolved(2)], {"data": {"nest": {"test": [1, 2]}}}
    )
    test_contains_null = check(
        [resolved(1), resolved(None), resolved(2)],
        {"data": {"nest": {"test": [1, None, 2]}}},
    )
    test_contains_reject = check(
        lambda: [resolved(1), rejected(Exception("bad")), resolved(2)],
        {
            "data": {"nest": {"test": [1, None, 2]}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "bad",
                }
            ],
        },
    )


class Test_NotNullListOfT_Array_T:  # [T]! Array<T>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))

    test_contains_values = check(resolved([1, 2]), {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        resolved([1, None, 2]), {"data": {"nest": {"test": [1, None, 2]}}}
    )
    test_returns_null = check(
        resolved(None),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )


class Test_NotNullListOfT_Promise_Array_T:  # [T]! Promise<Array<T>>>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))

    test_contains_values = check(resolved([1, 2]), {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        resolved([1, None, 2]), {"data": {"nest": {"test": [1, None, 2]}}}
    )
    test_returns_null = check(
        resolved(None),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )

    test_rejected = check(
        lambda: rejected(Exception("bad")),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "bad",
                }
            ],
        },
    )


class Test_NotNullListOfT_Array_Promise_T:  # [T]! Promise<Array<T>>>
    type = GraphQLNonNull(GraphQLList(GraphQLInt))
    test_contains_values = check(
        [resolved(1), resolved(2)], {"data": {"nest": {"test": [1, 2]}}}
    )
    test_contains_null = check(
        [resolved(1), resolved(None), resolved(2)],
        {"data": {"nest": {"test": [1, None, 2]}}},
    )
    test_contains_reject = check(
        lambda: [resolved(1), rejected(Exception("bad")), resolved(2)],
        {
            "data": {"nest": {"test": [1, None, 2]}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "bad",
                }
            ],
        },
    )


class TestListOfNotNullT_Array_T:  # [T!] Array<T>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_values = check([1, 2], {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        [1, None, 2],
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )
    test_returns_null = check(None, {"data": {"nest": {"test": None}}})


class TestListOfNotNullT_Promise_Array_T:  # [T!] Promise<Array<T>>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_value = check(resolved([1, 2]), {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        resolved([1, None, 2]),
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )

    test_returns_null = check(resolved(None), {"data": {"nest": {"test": None}}})

    test_rejected = check(
        lambda: rejected(Exception("bad")),
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "bad",
                }
            ],
        },
    )


class TestListOfNotNullT_Array_Promise_T:  # [T!] Array<Promise<T>>
    type = GraphQLList(GraphQLNonNull(GraphQLInt))

    test_contains_values = check(
        [resolved(1), resolved(2)], {"data": {"nest": {"test": [1, 2]}}}
    )
    test_contains_null = check(
        [resolved(1), resolved(None), resolved(2)],
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )
    test_contains_reject = check(
        lambda: [resolved(1), rejected(Exception("bad")), resolved(2)],
        {
            "data": {"nest": {"test": None}},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "bad",
                }
            ],
        },
    )


class TestNotNullListOfNotNullT_Array_T:  # [T!]! Array<T>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_values = check([1, 2], {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        [1, None, 2],
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )
    test_returns_null = check(
        None,
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )


class TestNotNullListOfNotNullT_Promise_Array_T:  # [T!]! Promise<Array<T>>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_value = check(resolved([1, 2]), {"data": {"nest": {"test": [1, 2]}}})
    test_contains_null = check(
        resolved([1, None, 2]),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )

    test_returns_null = check(
        resolved(None),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )

    test_rejected = check(
        lambda: rejected(Exception("bad")),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test"],
                    "message": "bad",
                }
            ],
        },
    )


class TestNotNullListOfNotNullT_Array_Promise_T:  # [T!]! Array<Promise<T>>
    type = GraphQLNonNull(GraphQLList(GraphQLNonNull(GraphQLInt)))

    test_contains_values = check(
        [resolved(1), resolved(2)], {"data": {"nest": {"test": [1, 2]}}}
    )
    test_contains_null = check(
        [resolved(1), resolved(None), resolved(2)],
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "Cannot return null for non-nullable field DataType.test.",
                }
            ],
        },
    )
    test_contains_reject = check(
        lambda: [resolved(1), rejected(Exception("bad")), resolved(2)],
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 10, "line": 1}],
                    "path": ["nest", "test", 1],
                    "message": "bad",
                }
            ],
        },
    )
