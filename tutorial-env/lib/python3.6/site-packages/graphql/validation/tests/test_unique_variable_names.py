from graphql.language.location import SourceLocation
from graphql.validation.rules import UniqueVariableNames

from .utils import expect_fails_rule, expect_passes_rule


def duplicate_var(op_name, l1, c1, l2, c2):
    return {
        "message": UniqueVariableNames.duplicate_variable_message(op_name),
        "locations": [SourceLocation(l1, c1), SourceLocation(l2, c2)],
    }


def test_unique_variable_names():
    expect_passes_rule(
        UniqueVariableNames,
        """
      query A($x: Int, $y: String) { __typename }
      query B($x: String, $y: Int) { __typename }
    """,
    )


def test_duplicate_variable_names():
    expect_fails_rule(
        UniqueVariableNames,
        """
      query A($x: Int, $x: Int, $x: String) { __typename }
      query B($x: String, $x: Int) { __typename }
      query C($x: Int, $x: Int) { __typename }
    """,
        [
            duplicate_var("x", 2, 16, 2, 25),
            duplicate_var("x", 2, 16, 2, 34),
            duplicate_var("x", 3, 16, 3, 28),
            duplicate_var("x", 4, 16, 4, 25),
        ],
    )
