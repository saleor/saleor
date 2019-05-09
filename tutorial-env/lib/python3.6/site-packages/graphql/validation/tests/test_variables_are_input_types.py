from graphql.language.location import SourceLocation
from graphql.validation.rules import VariablesAreInputTypes

from .utils import expect_fails_rule, expect_passes_rule


def non_input_type_on_variable(variable_name, type_name, line, col):
    return {
        "message": VariablesAreInputTypes.non_input_type_on_variable_message(
            variable_name, type_name
        ),
        "locations": [SourceLocation(line, col)],
    }


def test_input_types_are_valid():
    expect_passes_rule(
        VariablesAreInputTypes,
        """
      query Foo($a: String, $b: [Boolean!]!, $c: ComplexInput) {
        field(a: $a, b: $b, c: $c)
      }
    """,
    )


def test_output_types_are_invalid():
    expect_fails_rule(
        VariablesAreInputTypes,
        """
      query Foo($a: Dog, $b: [[CatOrDog!]]!, $c: Pet) {
        field(a: $a, b: $b, c: $c)
      }
    """,
        [
            non_input_type_on_variable("a", "Dog", 2, 21),
            non_input_type_on_variable("b", "[[CatOrDog!]]!", 2, 30),
            non_input_type_on_variable("c", "Pet", 2, 50),
        ],
    )
