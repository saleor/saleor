from graphql.language.location import SourceLocation
from graphql.validation.rules import FragmentsOnCompositeTypes

from .utils import expect_fails_rule, expect_passes_rule


def fragment_on_non_composite_error(frag_name, type_name, line, column):
    return {
        "message": FragmentsOnCompositeTypes.fragment_on_non_composite_error_message(
            frag_name, type_name
        ),
        "locations": [SourceLocation(line, column)],
    }


def inline_fragment_on_non_composite_error(type_name, line, column):
    return {
        "message": FragmentsOnCompositeTypes.inline_fragment_on_non_composite_error_message(
            type_name
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_object_is_valid_fragment_type():
    expect_passes_rule(
        FragmentsOnCompositeTypes,
        """
      fragment validFragment on Dog {
        barks
      }
    """,
    )


def test_interface_is_valid_fragment_type():
    expect_passes_rule(
        FragmentsOnCompositeTypes,
        """
      fragment validFragment on Pet {
        name
      }
    """,
    )


def test_object_is_valid_inline_fragment_type():
    expect_passes_rule(
        FragmentsOnCompositeTypes,
        """
      fragment validFragment on Pet {
        ... on Dog {
          barks
        }
      }
    """,
    )


def test_inline_fragment_without_type_is_valid():
    expect_passes_rule(
        FragmentsOnCompositeTypes,
        """
    fragment validFragment on Pet {
      ... {
        name
      }
    }
    """,
    )


def test_union_is_valid_fragment_type():
    expect_passes_rule(
        FragmentsOnCompositeTypes,
        """
      fragment validFragment on CatOrDog {
        __typename
      }
    """,
    )


def test_scalar_is_invalid_fragment_type():
    expect_fails_rule(
        FragmentsOnCompositeTypes,
        """
      fragment scalarFragment on Boolean {
        bad
      }
    """,
        [fragment_on_non_composite_error("scalarFragment", "Boolean", 2, 34)],
    )


def test_enum_is_invalid_fragment_type():
    expect_fails_rule(
        FragmentsOnCompositeTypes,
        """
      fragment scalarFragment on FurColor {
        bad
      }
    """,
        [fragment_on_non_composite_error("scalarFragment", "FurColor", 2, 34)],
    )


def test_input_object_is_invalid_fragment_type():
    expect_fails_rule(
        FragmentsOnCompositeTypes,
        """
      fragment inputFragment on ComplexInput {
        stringField
      }
    """,
        [fragment_on_non_composite_error("inputFragment", "ComplexInput", 2, 33)],
    )


def test_scalar_is_invalid_inline_fragment_type():
    expect_fails_rule(
        FragmentsOnCompositeTypes,
        """
      fragment invalidFragment on Pet {
        ... on String {
          barks
        }
      }
    """,
        [inline_fragment_on_non_composite_error("String", 3, 16)],
    )
