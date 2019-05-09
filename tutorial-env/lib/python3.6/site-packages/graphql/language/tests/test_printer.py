import copy

from pytest import raises

from graphql.language.ast import Field, Name
from graphql.language.parser import parse
from graphql.language.printer import print_ast

from .fixtures import KITCHEN_SINK


def test_does_not_alter_ast():
    # type: () -> None
    ast = parse(KITCHEN_SINK)
    ast_copy = copy.deepcopy(ast)
    print_ast(ast)
    assert ast == ast_copy


def test_prints_minimal_ast():
    # type: () -> None
    ast = Field(name=Name(loc=None, value="foo"))
    assert print_ast(ast) == "foo"


def test_produces_helpful_error_messages():
    # type: () -> None
    bad_ast = {"random": "Data"}
    with raises(Exception) as excinfo:
        print_ast(bad_ast)
    assert "Invalid AST Node" in str(excinfo.value)


def test_correctly_prints_query_operation_without_name():
    # type: () -> None
    query_ast_shorthanded = parse("query { id, name }")
    assert (
        print_ast(query_ast_shorthanded)
        == """{
  id
  name
}
"""
    )


def test_correctly_prints_mutation_operation_without_name():
    # type: () -> None
    mutation_ast = parse("mutation { id, name }")
    assert (
        print_ast(mutation_ast)
        == """mutation {
  id
  name
}
"""
    )


def test_correctly_prints_query_with_artifacts():
    # type: () -> None
    query_ast_shorthanded = parse("query ($foo: TestType) @testDirective { id, name }")
    assert (
        print_ast(query_ast_shorthanded)
        == """query ($foo: TestType) @testDirective {
  id
  name
}
"""
    )


def test_correctly_prints_mutation_with_artifacts():
    # type: () -> None
    query_ast_shorthanded = parse(
        "mutation ($foo: TestType) @testDirective { id, name }"
    )
    assert (
        print_ast(query_ast_shorthanded)
        == """mutation ($foo: TestType) @testDirective {
  id
  name
}
"""
    )


def test_prints_kitchen_sink():
    # type: () -> None
    ast = parse(KITCHEN_SINK)
    printed = print_ast(ast)
    assert (
        printed
        == """query queryName($foo: ComplexType, $site: Site = MOBILE) {
  whoever123is: node(id: [123, 456]) {
    id
    ... on User @defer {
      field2 {
        id
        alias: field1(first: 10, after: $foo) @include(if: $foo) {
          id
          ...frag
        }
      }
    }
    ... @skip(unless: $foo) {
      id
    }
    ... {
      id
    }
  }
}

mutation likeStory {
  like(story: 123) @defer {
    story {
      id
    }
  }
}

subscription StoryLikeSubscription($input: StoryLikeSubscribeInput) {
  storyLikeSubscribe(input: $input) {
    story {
      likers {
        count
      }
      likeSentence {
        text
      }
    }
  }
}

fragment frag on Friend {
  foo(size: $size, bar: $b, obj: {key: "value"})
}

{
  unnamed(truthy: true, falsey: false)
  query
}
"""
    )
