# type: ignore
from graphql.error import format_error
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

from .utils import rejected, resolved

# Necessary for static type checking
if False:  # flake8: noqa
    from promise import Promise
    from typing import Any, Optional, Dict, Tuple, Union

sync_error = Exception("sync")
non_null_sync_error = Exception("nonNullSync")
promise_error = Exception("promise")
non_null_promise_error = Exception("nonNullPromise")


class ThrowingData(object):
    def sync(self):
        # type: () -> None
        raise sync_error

    def nonNullSync(self):
        # type: () -> None
        raise non_null_sync_error

    def promise(self):
        # type: () -> Promise
        return rejected(promise_error)

    def nonNullPromise(self):
        # type: () -> Promise
        return rejected(non_null_promise_error)

    def nest(self):
        # type: () -> ThrowingData
        return ThrowingData()

    def nonNullNest(self):
        # type: () -> ThrowingData
        return ThrowingData()

    def promiseNest(self):
        # type: () -> Promise
        return resolved(ThrowingData())

    def nonNullPromiseNest(self):
        # type: () -> Promise
        return resolved(ThrowingData())


class NullingData(object):
    def sync(self):
        # type: () -> Optional[Any]
        return None

    def nonNullSync(self):
        # type: () -> Optional[Any]
        return None

    def promise(self):
        # type: () -> Promise
        return resolved(None)

    def nonNullPromise(self):
        # type: () -> Promise
        return resolved(None)

    def nest(self):
        # type: () -> NullingData
        return NullingData()

    def nonNullNest(self):
        # type: () -> NullingData
        return NullingData()

    def promiseNest(self):
        # type: () -> Promise
        return resolved(NullingData())

    def nonNullPromiseNest(self):
        # type: () -> Promise
        return resolved(NullingData())


DataType = GraphQLObjectType(
    "DataType",
    lambda: {
        "sync": GraphQLField(GraphQLString),
        "nonNullSync": GraphQLField(GraphQLNonNull(GraphQLString)),
        "promise": GraphQLField(GraphQLString),
        "nonNullPromise": GraphQLField(GraphQLNonNull(GraphQLString)),
        "nest": GraphQLField(DataType),
        "nonNullNest": GraphQLField(GraphQLNonNull(DataType)),
        "promiseNest": GraphQLField(DataType),
        "nonNullPromiseNest": GraphQLField(GraphQLNonNull(DataType)),
    },
)

schema = GraphQLSchema(DataType)


def order_errors(error):
    # type: (Dict[str, Any]) -> Tuple[int, int]
    locations = error["locations"]
    return (locations[0]["column"], locations[0]["line"])


def check(doc, data, expected):
    # type: (str, Union[NullingData, ThrowingData], Dict[str, Any]) -> None
    ast = parse(doc)
    response = execute(schema, ast, data)

    if response.errors:
        result = {
            "data": response.data,
            "errors": [format_error(e) for e in response.errors],
        }
        if result["errors"] != expected["errors"]:
            assert result["data"] == expected["data"]
            # Sometimes the fields resolves asynchronously, so
            # we need to check that the errors are the same, but might be
            # raised in a different order.
            assert sorted(result["errors"], key=order_errors) == sorted(
                expected["errors"], key=order_errors
            )
        else:
            assert result == expected
    else:
        result = {"data": response.data}

        assert result == expected


def test_nulls_a_nullable_field_that_throws_sync():
    # type: () -> None
    doc = """
        query Q {
            sync
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"sync": None},
            "errors": [
                {
                    "locations": [{"column": 13, "line": 3}],
                    "path": ["sync"],
                    "message": str(sync_error),
                }
            ],
        },
    )


def test_nulls_a_nullable_field_that_throws_in_a_promise():
    # type: () -> None
    doc = """
        query Q {
            promise
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"promise": None},
            "errors": [
                {
                    "locations": [{"column": 13, "line": 3}],
                    "path": ["promise"],
                    "message": str(promise_error),
                }
            ],
        },
    )


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_throws():
    # type: () -> None
    doc = """
        query Q {
            nest {
                nonNullSync,
            }
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["nest", "nonNullSync"],
                    "message": str(non_null_sync_error),
                }
            ],
        },
    )


def test_nulls_a_synchronously_returned_object_that_contains_a_non_nullable_field_that_throws_in_a_promise():
    # type: () -> None
    doc = """
        query Q {
            nest {
                nonNullPromise,
            }
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["nest", "nonNullPromise"],
                    "message": str(non_null_promise_error),
                }
            ],
        },
    )


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_throws_synchronously():
    # type: () -> None
    doc = """
        query Q {
            promiseNest {
                nonNullSync,
            }
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"promiseNest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["promiseNest", "nonNullSync"],
                    "message": str(non_null_sync_error),
                }
            ],
        },
    )


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_throws_in_a_promise():
    # type: () -> None
    doc = """
        query Q {
            promiseNest {
                nonNullPromise,
            }
        }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": {"promiseNest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["promiseNest", "nonNullPromise"],
                    "message": str(non_null_promise_error),
                }
            ],
        },
    )


def test_nulls_a_complex_tree_of_nullable_fields_that_throw():
    # type: () -> None
    doc = """
      query Q {
        nest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
        promiseNest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
      }
    """
    check(
        doc,
        ThrowingData(),
        {
            "data": {
                "nest": {
                    "nest": {"promise": None, "sync": None},
                    "promise": None,
                    "promiseNest": {"promise": None, "sync": None},
                    "sync": None,
                },
                "promiseNest": {
                    "nest": {"promise": None, "sync": None},
                    "promise": None,
                    "promiseNest": {"promise": None, "sync": None},
                    "sync": None,
                },
            },
            "errors": [
                {
                    "locations": [{"column": 11, "line": 4}],
                    "path": ["nest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 11, "line": 5}],
                    "path": ["nest", "promise"],
                    "message": str(promise_error),
                },
                {
                    "locations": [{"column": 13, "line": 7}],
                    "path": ["nest", "nest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 13, "line": 8}],
                    "path": ["nest", "nest", "promise"],
                    "message": str(promise_error),
                },
                {
                    "locations": [{"column": 13, "line": 11}],
                    "path": ["nest", "promiseNest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 13, "line": 12}],
                    "path": ["nest", "promiseNest", "promise"],
                    "message": str(promise_error),
                },
                {
                    "locations": [{"column": 11, "line": 16}],
                    "path": ["promiseNest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 11, "line": 17}],
                    "path": ["promiseNest", "promise"],
                    "message": str(promise_error),
                },
                {
                    "locations": [{"column": 13, "line": 19}],
                    "path": ["promiseNest", "nest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 13, "line": 20}],
                    "path": ["promiseNest", "nest", "promise"],
                    "message": str(promise_error),
                },
                {
                    "locations": [{"column": 13, "line": 23}],
                    "path": ["promiseNest", "promiseNest", "sync"],
                    "message": str(sync_error),
                },
                {
                    "locations": [{"column": 13, "line": 24}],
                    "path": ["promiseNest", "promiseNest", "promise"],
                    "message": str(promise_error),
                },
            ],
        },
    )


def test_nulls_the_first_nullable_object_after_a_field_throws_in_a_long_chain_of_fields_that_are_non_null():
    # type: () -> None
    doc = """
    query Q {
        nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        anotherNest: nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
        anotherPromiseNest: promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
      }
    """
    check(
        doc,
        ThrowingData(),
        {
            "data": {
                "nest": None,
                "promiseNest": None,
                "anotherNest": None,
                "anotherPromiseNest": None,
            },
            "errors": [
                {
                    "locations": [{"column": 19, "line": 8}],
                    "path": [
                        "nest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullSync",
                    ],
                    "message": str(non_null_sync_error),
                },
                {
                    "locations": [{"column": 19, "line": 19}],
                    "path": [
                        "promiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullSync",
                    ],
                    "message": str(non_null_sync_error),
                },
                {
                    "locations": [{"column": 19, "line": 30}],
                    "path": [
                        "anotherNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullPromise",
                    ],
                    "message": str(non_null_promise_error),
                },
                {
                    "locations": [{"column": 19, "line": 41}],
                    "path": [
                        "anotherPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullPromise",
                    ],
                    "message": str(non_null_promise_error),
                },
            ],
        },
    )


def test_nulls_a_nullable_field_that_returns_null():
    # type: () -> None
    doc = """
        query Q {
            sync
        }
    """

    check(doc, NullingData(), {"data": {"sync": None}})


def test_nulls_a_nullable_field_that_returns_null_in_a_promise():
    # type: () -> None
    doc = """
        query Q {
            promise
        }
    """

    check(doc, NullingData(), {"data": {"promise": None}})


def test_nulls_a_sync_returned_object_that_contains_a_non_nullable_field_that_returns_null_synchronously():
    # type: () -> None
    doc = """
        query Q {
            nest {
                nonNullSync,
            }
        }
    """
    check(
        doc,
        NullingData(),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["nest", "nonNullSync"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullSync.",
                }
            ],
        },
    )


def test_nulls_a_synchronously_returned_object_that_contains_a_non_nullable_field_that_returns_null_in_a_promise():
    # type: () -> None
    doc = """
        query Q {
            nest {
                nonNullPromise,
            }
        }
    """
    check(
        doc,
        NullingData(),
        {
            "data": {"nest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["nest", "nonNullPromise"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullPromise.",
                }
            ],
        },
    )


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_returns_null_synchronously():
    # type: () -> None
    doc = """
        query Q {
            promiseNest {
                nonNullSync,
            }
        }
    """
    check(
        doc,
        NullingData(),
        {
            "data": {"promiseNest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["promiseNest", "nonNullSync"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullSync.",
                }
            ],
        },
    )


def test_nulls_an_object_returned_in_a_promise_that_contains_a_non_nullable_field_that_returns_null_ina_a_promise():
    # type: () -> None
    doc = """
        query Q {
            promiseNest {
                nonNullPromise
            }
        }
    """

    check(
        doc,
        NullingData(),
        {
            "data": {"promiseNest": None},
            "errors": [
                {
                    "locations": [{"column": 17, "line": 4}],
                    "path": ["promiseNest", "nonNullPromise"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullPromise.",
                }
            ],
        },
    )


def test_nulls_a_complex_tree_of_nullable_fields_that_returns_null():
    # type: () -> None
    doc = """
      query Q {
        nest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
        promiseNest {
          sync
          promise
          nest {
            sync
            promise
          }
          promiseNest {
            sync
            promise
          }
        }
      }
    """
    check(
        doc,
        NullingData(),
        {
            "data": {
                "nest": {
                    "sync": None,
                    "promise": None,
                    "nest": {"sync": None, "promise": None},
                    "promiseNest": {"sync": None, "promise": None},
                },
                "promiseNest": {
                    "sync": None,
                    "promise": None,
                    "nest": {"sync": None, "promise": None},
                    "promiseNest": {"sync": None, "promise": None},
                },
            }
        },
    )


def test_nulls_the_first_nullable_object_after_a_field_returns_null_in_a_long_chain_of_fields_that_are_non_null():
    # type: () -> None
    doc = """
      query Q {
        nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullSync
                }
              }
            }
          }
        }
        anotherNest: nest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
        anotherPromiseNest: promiseNest {
          nonNullNest {
            nonNullPromiseNest {
              nonNullNest {
                nonNullPromiseNest {
                  nonNullPromise
                }
              }
            }
          }
        }
      }
    """

    check(
        doc,
        NullingData(),
        {
            "data": {
                "nest": None,
                "promiseNest": None,
                "anotherNest": None,
                "anotherPromiseNest": None,
            },
            "errors": [
                {
                    "locations": [{"column": 19, "line": 8}],
                    "path": [
                        "nest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullSync",
                    ],
                    "message": "Cannot return null for non-nullable field DataType.nonNullSync.",
                },
                {
                    "locations": [{"column": 19, "line": 19}],
                    "path": [
                        "promiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullSync",
                    ],
                    "message": "Cannot return null for non-nullable field DataType.nonNullSync.",
                },
                {
                    "locations": [{"column": 19, "line": 30}],
                    "path": [
                        "anotherNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullPromise",
                    ],
                    "message": "Cannot return null for non-nullable field DataType.nonNullPromise.",
                },
                {
                    "locations": [{"column": 19, "line": 41}],
                    "path": [
                        "anotherPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullNest",
                        "nonNullPromiseNest",
                        "nonNullPromise",
                    ],
                    "message": "Cannot return null for non-nullable field DataType.nonNullPromise.",
                },
            ],
        },
    )


def test_nulls_the_top_level_if_sync_non_nullable_field_throws():
    # type: () -> None
    doc = """
        query Q { nonNullSync }
    """
    check(
        doc,
        ThrowingData(),
        {
            "data": None,
            "errors": [
                {
                    "locations": [{"column": 19, "line": 2}],
                    "path": ["nonNullSync"],
                    "message": str(non_null_sync_error),
                }
            ],
        },
    )


def test_nulls_the_top_level_if_async_non_nullable_field_errors():
    # type: () -> None
    doc = """
        query Q { nonNullPromise }
    """

    check(
        doc,
        ThrowingData(),
        {
            "data": None,
            "errors": [
                {
                    "locations": [{"column": 19, "line": 2}],
                    "path": ["nonNullPromise"],
                    "message": str(non_null_promise_error),
                }
            ],
        },
    )


def test_nulls_the_top_level_if_sync_non_nullable_field_returns_null():
    # type: () -> None
    doc = """
        query Q { nonNullSync }
    """
    check(
        doc,
        NullingData(),
        {
            "data": None,
            "errors": [
                {
                    "locations": [{"column": 19, "line": 2}],
                    "path": ["nonNullSync"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullSync.",
                }
            ],
        },
    )


def test_nulls_the_top_level_if_async_non_nullable_field_resolves_null():
    # type: () -> None
    doc = """
        query Q { nonNullPromise }
    """
    check(
        doc,
        NullingData(),
        {
            "data": None,
            "errors": [
                {
                    "locations": [{"column": 19, "line": 2}],
                    "path": ["nonNullPromise"],
                    "message": "Cannot return null for non-nullable field DataType.nonNullPromise.",
                }
            ],
        },
    )
