from graphql.language.location import SourceLocation
from graphql.validation.rules.fields_on_correct_type import (
    FieldsOnCorrectType,
    _undefined_field_message,
)

from .utils import expect_fails_rule, expect_passes_rule


def undefined_field(field, gql_type, suggested_types, suggested_fields, line, column):
    return {
        "message": _undefined_field_message(
            field, gql_type, suggested_types, suggested_fields
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_object_field_selection():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment objectFieldSelection on Dog {
        __typename
        name
      }
    """,
    )


def test_aliased_object_field_selection():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment aliasedObjectFieldSelection on Dog {
        tn : __typename
        otherName : name
      }
    """,
    )


def test_interface_field_selection():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment interfaceFieldSelection on Pet {
        __typename
        name
      }
    """,
    )


def test_aliased_interface_field_selection():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment interfaceFieldSelection on Pet {
        otherName : name
      }
    """,
    )


def test_lying_alias_selection():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment lyingAliasSelection on Dog {
        name : nickname
      }
    """,
    )


def test_ignores_fields_on_unknown_type():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment unknownSelection on UnknownType {
        unknownField
      }
    """,
    )


def test_reports_errors_when_type_is_known_again():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment typeKnownAgain on Pet {
        unknown_pet_field {
          ... on Cat {
            unknown_cat_field
          }
        }
      },
    """,
        [
            undefined_field("unknown_pet_field", "Pet", [], [], 3, 9),
            undefined_field("unknown_cat_field", "Cat", [], [], 5, 13),
        ],
    )


def test_field_not_defined_on_fragment():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment fieldNotDefined on Dog {
        meowVolume
      }
    """,
        [undefined_field("meowVolume", "Dog", [], ["barkVolume"], 3, 9)],
    )


def test_ignores_deeply_unknown_field():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment deepFieldNotDefined on Dog {
        unknown_field {
          deeper_unknown_field
        }
      }
    """,
        [undefined_field("unknown_field", "Dog", [], [], 3, 9)],
    )


def test_sub_field_not_defined():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment subFieldNotDefined on Human {
        pets {
          unknown_field
        }
      }
    """,
        [undefined_field("unknown_field", "Pet", [], [], 4, 11)],
    )


def test_field_not_defined_on_inline_fragment():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment fieldNotDefined on Pet {
        ... on Dog {
          meowVolume
        }
      }
    """,
        [undefined_field("meowVolume", "Dog", [], ["barkVolume"], 4, 11)],
    )


def test_aliased_field_target_not_defined():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment aliasedFieldTargetNotDefined on Dog {
        volume : mooVolume
      }
    """,
        [undefined_field("mooVolume", "Dog", [], ["barkVolume"], 3, 9)],
    )


def test_aliased_lying_field_target_not_defined():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment aliasedLyingFieldTargetNotDefined on Dog {
        barkVolume : kawVolume
      }
    """,
        [undefined_field("kawVolume", "Dog", [], ["barkVolume"], 3, 9)],
    )


def test_not_defined_on_interface():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment notDefinedOnInterface on Pet {
        tailLength
      }
    """,
        [undefined_field("tailLength", "Pet", [], [], 3, 9)],
    )


def test_defined_on_implementors_but_not_on_interface():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment definedOnImplementorsButNotInterface on Pet {
        nickname
      }
    """,
        [undefined_field("nickname", "Pet", ["Dog", "Cat"], ["name"], 3, 9)],
    )


def test_meta_field_selection_on_union():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment directFieldSelectionOnUnion on CatOrDog {
        __typename
      }
    """,
    )


def test_direct_field_selection_on_union():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment directFieldSelectionOnUnion on CatOrDog {
        directField
      }
    """,
        [undefined_field("directField", "CatOrDog", [], [], 3, 9)],
    )


def test_defined_on_implementors_queried_on_union():
    expect_fails_rule(
        FieldsOnCorrectType,
        """
      fragment definedOnImplementorsQueriedOnUnion on CatOrDog {
        name
      }
    """,
        [
            undefined_field(
                "name", "CatOrDog", ["Being", "Pet", "Canine", "Dog", "Cat"], [], 3, 9
            )
        ],
    )


def test_valid_field_in_inline_fragment():
    expect_passes_rule(
        FieldsOnCorrectType,
        """
      fragment objectFieldSelection on Pet {
        ... on Dog {
          name
        }
        ... {
          name
        }
      }
    """,
    )


def test_fields_correct_type_no_suggestion():
    message = _undefined_field_message("f", "T", [], [])
    assert message == 'Cannot query field "f" on type "T".'


def test_works_with_no_small_numbers_of_type_suggestion():
    message = _undefined_field_message("f", "T", ["A", "B"], [])
    assert message == (
        'Cannot query field "f" on type "T". '
        + 'Did you mean to use an inline fragment on "A" or "B"?'
    )


def test_works_with_no_small_numbers_of_field_suggestion():
    message = _undefined_field_message("f", "T", [], ["z", "y"])
    assert message == (
        'Cannot query field "f" on type "T". ' + 'Did you mean "z" or "y"?'
    )


def test_only_shows_one_set_of_suggestions_at_a_time_preferring_types():
    message = _undefined_field_message("f", "T", ["A", "B"], ["z", "y"])
    assert message == (
        'Cannot query field "f" on type "T". '
        + 'Did you mean to use an inline fragment on "A" or "B"?'
    )


def test_limits_lots_of_type_suggestions():
    message = _undefined_field_message("f", "T", ["A", "B", "C", "D", "E", "F"], [])
    assert message == (
        'Cannot query field "f" on type "T". '
        + 'Did you mean to use an inline fragment on "A", "B", "C", "D" or "E"?'
    )


def test_limits_lots_of_field_suggestions():
    message = _undefined_field_message("f", "T", [], ["z", "y", "x", "w", "v", "u"])
    assert message == (
        'Cannot query field "f" on type "T". '
        + 'Did you mean "z", "y", "x", "w" or "v"?'
    )
