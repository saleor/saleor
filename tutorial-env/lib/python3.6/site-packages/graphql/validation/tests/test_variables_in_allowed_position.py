from graphql.language.location import SourceLocation
from graphql.validation.rules import VariablesInAllowedPosition

from .utils import expect_fails_rule, expect_passes_rule


def test_boolean_boolean():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($booleanArg: Boolean)
      {
        complicatedArgs {
          booleanArgField(booleanArg: $booleanArg)
        }
      }
    """,
    )


def test_boolean_boolean_in_fragment():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      fragment booleanArgFrag on ComplicatedArgs {
        booleanArgField(booleanArg: $booleanArg)
      }

      query Query($booleanArg: Boolean)
      {
        complicatedArgs {
          ...booleanArgFrag
        }
      }
    """,
    )

    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($booleanArg: Boolean)
      {
        complicatedArgs {
          ...booleanArgFrag
        }
      }
      fragment booleanArgFrag on ComplicatedArgs {
        booleanArgField(booleanArg: $booleanArg)
      }
    """,
    )


def test_non_null_boolean_boolean():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($nonNullBooleanArg: Boolean!)
      {
        complicatedArgs {
          booleanArgField(booleanArg: $nonNullBooleanArg)
        }
      }
    """,
    )


def test_non_null_boolean_to_boolean_within_fragment():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      fragment booleanArgFrag on ComplicatedArgs {
        booleanArgField(booleanArg: $nonNullBooleanArg)
      }
      query Query($nonNullBooleanArg: Boolean!)
      {
        complicatedArgs {
          ...booleanArgFrag
        }
      }
    """,
    )


def test_int_non_null_int_with_default():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($intArg: Int = 1)
      {
        complicatedArgs {
          nonNullIntArgField(nonNullIntArg: $intArg)
        }
      }
    """,
    )


def test_string_string():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringListVar: [String])
      {
        complicatedArgs {
          stringListArgField(stringListArg: $stringListVar)
        }
      }
    """,
    )


def test_non_null_string_string():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringListVar: [String!])
      {
        complicatedArgs {
          stringListArgField(stringListArg: $stringListVar)
        }
      }
    """,
    )


def test_string_string_item_position():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringVar: String)
      {
        complicatedArgs {
          stringListArgField(stringListArg: [$stringVar])
        }
      }
    """,
    )


def test_non_null_string_string_item_positiion():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringVar: String!)
      {
        complicatedArgs {
          stringListArgField(stringListArg: [$stringVar])
        }
      }
    """,
    )


def test_complex_input_complex_input():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($complexVar: ComplexInput)
      {
        complicatedArgs {
          complexArgField(complexArg: $complexVar)
        }
      }
    """,
    )


def test_complex_input_complex_input_in_field_position():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($boolVar: Boolean = false)
      {
        complicatedArgs {
          complexArgField(complexArg: {requiredArg: $boolVar})
        }
      }
    """,
    )


def test_boolean_non_null_boolean_in_directive():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($boolVar: Boolean!)
      {
        dog @include(if: $boolVar)
      }
    """,
    )


def test_boolean_non_null_boolean_in_directive_with_default():
    expect_passes_rule(
        VariablesInAllowedPosition,
        """
      query Query($boolVar: Boolean = false)
      {
        dog @include(if: $boolVar)
      }
    """,
    )


def test_int_non_null_int():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      query Query($intArg: Int) {
        complicatedArgs {
          nonNullIntArgField(nonNullIntArg: $intArg)
        }
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "intArg", "Int", "Int!"
                ),
                "locations": [SourceLocation(4, 45), SourceLocation(2, 19)],
            }
        ],
    )


def test_int_non_null_int_within_fragment():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      fragment nonNullIntArgFieldFrag on ComplicatedArgs {
        nonNullIntArgField(nonNullIntArg: $intArg)
      }
      query Query($intArg: Int) {
        complicatedArgs {
          ...nonNullIntArgFieldFrag
        }
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "intArg", "Int", "Int!"
                ),
                "locations": [SourceLocation(5, 19), SourceLocation(3, 43)],
            }
        ],
    )


def test_int_non_null_int_within_nested_fragment():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      fragment outerFrag on ComplicatedArgs {
        ...nonNullIntArgFieldFrag
      }
      fragment nonNullIntArgFieldFrag on ComplicatedArgs {
        nonNullIntArgField(nonNullIntArg: $intArg)
      }
      query Query($intArg: Int) {
        complicatedArgs {
          ...outerFrag
        }
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "intArg", "Int", "Int!"
                ),
                "locations": [SourceLocation(8, 19), SourceLocation(6, 43)],
            }
        ],
    )


def test_string_over_boolean():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringVar: String) {
        complicatedArgs {
          booleanArgField(booleanArg: $stringVar)
        }
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "stringVar", "String", "Boolean"
                ),
                "locations": [SourceLocation(2, 19), SourceLocation(4, 39)],
            }
        ],
    )


def test_string_string_fail():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringVar: String) {
        complicatedArgs {
          stringListArgField(stringListArg: $stringVar)
        }
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "stringVar", "String", "[String]"
                ),
                "locations": [SourceLocation(2, 19), SourceLocation(4, 45)],
            }
        ],
    )


def test_boolean_non_null_boolean_in_directive():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      query Query($boolVar: Boolean) {
        dog @include(if: $boolVar)
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "boolVar", "Boolean", "Boolean!"
                ),
                "locations": [SourceLocation(2, 19), SourceLocation(3, 26)],
            }
        ],
    )


def test_string_non_null_boolean_in_directive():
    expect_fails_rule(
        VariablesInAllowedPosition,
        """
      query Query($stringVar: String) {
        dog @include(if: $stringVar)
      }
    """,
        [
            {
                "message": VariablesInAllowedPosition.bad_var_pos_message(
                    "stringVar", "String", "Boolean!"
                ),
                "locations": [SourceLocation(2, 19), SourceLocation(3, 26)],
            }
        ],
    )
