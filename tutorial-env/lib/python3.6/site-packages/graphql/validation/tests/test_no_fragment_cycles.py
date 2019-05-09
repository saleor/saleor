from graphql.language.location import SourceLocation as L
from graphql.validation.rules import NoFragmentCycles

from .utils import expect_fails_rule, expect_passes_rule


def cycle_error_message(fragment_name, spread_names, *locations):
    return {
        "message": NoFragmentCycles.cycle_error_message(fragment_name, spread_names),
        "locations": list(locations),
    }


def test_single_reference_is_valid():
    expect_passes_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB }
    fragment fragB on Dog { name }
    """,
    )


def test_spreading_twice_is_not_circular():
    expect_passes_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB, ...fragB }
    fragment fragB on Dog { name }
    """,
    )


def test_spreading_twice_indirectly_is_not_circular():
    expect_passes_rule(
        NoFragmentCycles,
        """
      fragment fragA on Dog { ...fragB, ...fragC }
      fragment fragB on Dog { ...fragC }
      fragment fragC on Dog { name }
    """,
    )


def test_double_spread_within_abstract_types():
    expect_passes_rule(
        NoFragmentCycles,
        """
      fragment nameFragment on Pet {
        ... on Dog { name }
        ... on Cat { name }
      }
      fragment spreadsInAnon on Pet {
        ... on Dog { ...nameFragment }
        ... on Cat { ...nameFragment }
      }
    """,
    )


def test_does_not_raise_false_positive_on_unknown_fragment():
    expect_passes_rule(
        NoFragmentCycles,
        """
      fragment nameFragment on Pet {
        ...UnknownFragment
      }
    """,
    )


def test_spreading_recursively_within_field_fails():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Human { relatives { ...fragA } },
    """,
        [cycle_error_message("fragA", [], L(2, 43))],
    )


def test_no_spreading_itself_directly():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragA }
    """,
        [cycle_error_message("fragA", [], L(2, 29))],
    )


def test_no_spreading_itself_directly_within_inline_fragment():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Pet {
        ... on Dog {
            ...fragA
        }
    }
    """,
        [cycle_error_message("fragA", [], L(4, 13))],
    )


def test_no_spreading_itself_indirectly():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB }
    fragment fragB on Dog { ...fragA }
    """,
        [cycle_error_message("fragA", ["fragB"], L(2, 29), L(3, 29))],
    )


def test_no_spreading_itself_indirectly_reports_opposite_order():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragB on Dog { ...fragA }
    fragment fragA on Dog { ...fragB }
    """,
        [cycle_error_message("fragB", ["fragA"], L(2, 29), L(3, 29))],
    )


def test_no_spreading_itself_indirectly_within_inline_fragment():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Pet {
        ... on Dog {
            ...fragB
        }
    }
    fragment fragB on Pet {
        ... on Dog {
            ...fragA
        }
    }
    """,
        [cycle_error_message("fragA", ["fragB"], L(4, 13), L(9, 13))],
    )


def test_no_spreading_itself_deeply():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB }
    fragment fragB on Dog { ...fragC }
    fragment fragC on Dog { ...fragO }
    fragment fragX on Dog { ...fragY }
    fragment fragY on Dog { ...fragZ }
    fragment fragZ on Dog { ...fragO }
    fragment fragO on Dog { ...fragP }
    fragment fragP on Dog { ...fragA, ...fragX }
    """,
        [
            cycle_error_message(
                "fragA",
                ["fragB", "fragC", "fragO", "fragP"],
                L(2, 29),
                L(3, 29),
                L(4, 29),
                L(8, 29),
                L(9, 29),
            ),
            cycle_error_message(
                "fragO",
                ["fragP", "fragX", "fragY", "fragZ"],
                L(8, 29),
                L(9, 39),
                L(5, 29),
                L(6, 29),
                L(7, 29),
            ),
        ],
    )


def test_no_spreading_itself_deeply_two_paths():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB, ...fragC }
    fragment fragB on Dog { ...fragA }
    fragment fragC on Dog { ...fragA }
    """,
        [
            cycle_error_message("fragA", ["fragB"], L(2, 29), L(3, 29)),
            cycle_error_message("fragA", ["fragC"], L(2, 39), L(4, 29)),
        ],
    )


def test_no_spreading_itself_deeply_two_paths_alt_reverse_order():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragC }
    fragment fragB on Dog { ...fragC }
    fragment fragC on Dog { ...fragA, ...fragB }
    """,
        [
            cycle_error_message("fragA", ["fragC"], L(2, 29), L(4, 29)),
            cycle_error_message("fragC", ["fragB"], L(4, 39), L(3, 29)),
        ],
    )


def test_no_spreading_itself_deeply_and_immediately():
    expect_fails_rule(
        NoFragmentCycles,
        """
    fragment fragA on Dog { ...fragB }
    fragment fragB on Dog { ...fragB, ...fragC }
    fragment fragC on Dog { ...fragA, ...fragB }
    """,
        [
            cycle_error_message("fragB", [], L(3, 29)),
            cycle_error_message(
                "fragA", ["fragB", "fragC"], L(2, 29), L(3, 39), L(4, 29)
            ),
            cycle_error_message("fragB", ["fragC"], L(3, 39), L(4, 39)),
        ],
    )
