from graphql.language.location import SourceLocation
from graphql.validation.rules.known_type_names import (
    KnownTypeNames,
    _unknown_type_message,
)

from .utils import expect_fails_rule, expect_passes_rule


def unknown_type(type_name, suggested_types, line, column):
    return {
        "message": _unknown_type_message(type_name, suggested_types),
        "locations": [SourceLocation(line, column)],
    }


def test_known_type_names_are_valid():
    expect_passes_rule(
        KnownTypeNames,
        """
      query Foo($var: String, $required: [String!]!) {
        user(id: 4) {
          pets { ... on Pet { name }, ...PetFields, ... { name } }
        }
      }
      fragment PetFields on Pet {
        name
      }
    """,
    )


def test_unknown_type_names_are_invalid():
    expect_fails_rule(
        KnownTypeNames,
        """
      query Foo($var: JumbledUpLetters) {
        user(id: 4) {
          name
          pets { ... on Badger { name }, ...PetFields, ... { name } }
        }
      }
      fragment PetFields on Peettt {
        name
      }
    """,
        [
            unknown_type("JumbledUpLetters", [], 2, 23),
            unknown_type("Badger", [], 5, 25),
            unknown_type("Peettt", ["Pet"], 8, 29),
        ],
    )


def test_ignores_type_definitions():
    expect_fails_rule(
        KnownTypeNames,
        """
      type NotInTheSchema {
        field: FooBar
      }
      interface FooBar {
        field: NotInTheSchema
      }
      union U = A | B
      input Blob {
        field: UnknownType
      }
      query Foo($var: NotInTheSchema) {
        user(id: $var) {
          id
        }
      }
    """,
        [unknown_type("NotInTheSchema", [], 12, 23)],
    )
