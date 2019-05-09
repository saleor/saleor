from copy import deepcopy

from pytest import raises

from graphql import parse
from graphql.language import ast
from graphql.language.printer import print_ast

from .fixtures import SCHEMA_KITCHEN_SINK


def test_prints_minimal_ast():
    # type: () -> None
    node = ast.ScalarTypeDefinition(name=ast.Name("foo"))

    assert print_ast(node) == "scalar foo"


def test_print_produces_helpful_error_messages():
    # type: () -> None
    bad_ast = {"random": "Data"}
    with raises(AssertionError) as excinfo:
        print_ast(bad_ast)

    assert "Invalid AST Node: {'random': 'Data'}" in str(excinfo.value)


def test_does_not_alter_ast():
    # type: () -> None
    ast = parse(SCHEMA_KITCHEN_SINK)
    ast_copy = deepcopy(ast)
    print_ast(ast)
    assert ast == ast_copy


def test_prints_kitchen_sink():
    # type: () -> None
    ast = parse(SCHEMA_KITCHEN_SINK)
    printed = print_ast(ast)

    expected = """schema {
  query: QueryType
  mutation: MutationType
}

type Foo implements Bar {
  one: Type
  two(argument: InputType!): Type
  three(argument: InputType, other: String): Int
  four(argument: String = "string"): String
  five(argument: [String] = ["string", "string"]): String
  six(argument: InputType = {key: "value"}): Type
}

type AnnotatedObject @onObject(arg: "value") {
  annotatedField(arg: Type = "default" @onArg): Type @onField
}

interface Bar {
  one: Type
  four(argument: String = "string"): String
}

interface AnnotatedInterface @onInterface {
  annotatedField(arg: Type @onArg): Type @onField
}

union Feed = Story | Article | Advert

union AnnotatedUnion @onUnion = A | B

scalar CustomScalar

scalar AnnotatedScalar @onScalar

enum Site {
  DESKTOP
  MOBILE
}

enum AnnotatedEnum @onEnum {
  ANNOTATED_VALUE @onEnumValue
  OTHER_VALUE
}

input InputType {
  key: String!
  answer: Int = 42
}

input AnnotatedInput @onInputObjectType {
  annotatedField: Type @onField
}

extend type Foo {
  seven(argument: [String]): Type
}

extend type Foo @onType {}

type NoFields {}

directive @skip(if: Boolean!) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT

directive @include(if: Boolean!) on FIELD | FRAGMENT_SPREAD | INLINE_FRAGMENT
"""

    assert printed == expected
