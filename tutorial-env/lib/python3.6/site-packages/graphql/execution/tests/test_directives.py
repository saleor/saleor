# type: ignore
from graphql.execution import execute
from graphql.language.parser import parse
from graphql.type import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString

schema = GraphQLSchema(
    query=GraphQLObjectType(
        name="TestType",
        fields={"a": GraphQLField(GraphQLString), "b": GraphQLField(GraphQLString)},
    )
)


class Data(object):
    a = "a"
    b = "b"


def execute_test_query(doc):
    # type: (str) -> ExecutionResult
    return execute(schema, parse(doc), Data)


def test_basic_query_works():
    # type: () -> None
    result = execute_test_query("{ a, b }")
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_if_true_includes_scalar():
    # type: () -> None
    result = execute_test_query("{ a, b @include(if: true) }")
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_if_false_omits_on_scalar():
    # type: () -> None
    result = execute_test_query("{ a, b @include(if: false) }")
    assert not result.errors
    assert result.data == {"a": "a"}


def test_skip_false_includes_scalar():
    # type: () -> None
    result = execute_test_query("{ a, b @skip(if: false) }")
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_skip_true_omits_scalar():
    # type: () -> None
    result = execute_test_query("{ a, b @skip(if: true) }")
    assert not result.errors
    assert result.data == {"a": "a"}


def test_if_false_omits_fragment_spread():
    # type: () -> None
    q = """
        query Q {
          a
          ...Frag @include(if: false)
        }
        fragment Frag on TestType {
          b
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_if_true_includes_fragment_spread():
    # type: () -> None
    q = """
        query Q {
          a
          ...Frag @include(if: true)
        }
        fragment Frag on TestType {
          b
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_skip_false_includes_fragment_spread():
    # type: () -> None
    q = """
        query Q {
          a
          ...Frag @skip(if: false)
        }
        fragment Frag on TestType {
          b
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_skip_true_omits_fragment_spread():
    # type: () -> None
    q = """
        query Q {
          a
          ...Frag @skip(if: true)
        }
        fragment Frag on TestType {
          b
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_if_false_omits_inline_fragment():
    # type: () -> None
    q = """
        query Q {
          a
          ... on TestType @include(if: false) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_if_true_includes_inline_fragment():
    # type: () -> None
    q = """
        query Q {
          a
          ... on TestType @include(if: true) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_skip_false_includes_inline_fragment():
    # type: () -> None
    q = """
        query Q {
          a
          ... on TestType @skip(if: false) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_skip_true_omits_inline_fragment():
    # type: () -> None
    q = """
        query Q {
          a
          ... on TestType @skip(if: true) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_skip_true_omits_fragment():
    # type: () -> None
    q = """
        query Q {
          a
          ...Frag
        }
        fragment Frag on TestType @skip(if: true) {
          b
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_skip_on_inline_anonymous_fragment_omits_field():
    # type: () -> None
    q = """
        query Q {
          a
          ... @skip(if: true) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_skip_on_inline_anonymous_fragment_does_not_omit_field():
    # type: () -> None
    q = """
        query Q {
          a
          ... @skip(if: false) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_include_on_inline_anonymous_fragment_omits_field():
    # type: () -> None
    q = """
        query Q {
          a
          ... @include(if: false) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a"}


def test_include_on_inline_anonymous_fragment_does_not_omit_field():
    # type: () -> None
    q = """
        query Q {
          a
          ... @include(if: true) {
            b
          }
        }
    """
    result = execute_test_query(q)
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_works_directives_include_and_no_skip():
    # type: () -> None
    result = execute_test_query("{ a, b @include(if: true) @skip(if: false) }")
    assert not result.errors
    assert result.data == {"a": "a", "b": "b"}


def test_works_directives_include_and_skip():
    # type: () -> None
    result = execute_test_query("{ a, b @include(if: true) @skip(if: true) }")
    assert not result.errors
    assert result.data == {"a": "a"}


def test_works_directives_no_include_or_skip():
    # type: () -> None
    result = execute_test_query("{ a, b @include(if: false) @skip(if: false) }")
    assert not result.errors
    assert result.data == {"a": "a"}
