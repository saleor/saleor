from graphql.language.location import SourceLocation
from graphql.validation.rules import UniqueArgumentNames

from .utils import expect_fails_rule, expect_passes_rule


def duplicate_arg(arg_name, l1, c1, l2, c2):
    return {
        "message": UniqueArgumentNames.duplicate_arg_message(arg_name),
        "locations": [SourceLocation(l1, c1), SourceLocation(l2, c2)],
    }


def test_no_arguments_on_field():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field
      }
    """,
    )


def test_no_arguments_on_directive():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field
      }
    """,
    )


def test_argument_on_field():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field(arg: "value")
      }
    """,
    )


def test_argument_on_directive():
    expect_passes_rule(
        UniqueArgumentNames,
        """
       {
        field @directive(arg: "value")
      }
    """,
    )


def test_same_field_two_arguments():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        one: field(arg: "value")
        two: field(arg: "value")
      }
    """,
    )


def test_same_argument_on_field_and_directive():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field(arg: "value") @directive(arg: "value")
      }
    """,
    )


def test_same_argument_two_directives():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field @directive1(arg: "value") @directive2(arg: "value")
      }
    """,
    )


def test_multiple_field_arguments():
    expect_passes_rule(
        UniqueArgumentNames,
        """
      {
        field(arg1: "value", arg2: "value", arg3: "value")
      }
    """,
    )


def test_multiple_directive_arguments():
    expect_passes_rule(
        UniqueArgumentNames,
        """
    {
      field @directive(arg1: "value", arg2: "value", arg3: "value")
    }
    """,
    )


def test_duplicate_field_arguments():
    expect_fails_rule(
        UniqueArgumentNames,
        """
    {
      field(arg1: "value", arg1: "value")
    }
    """,
        [duplicate_arg("arg1", 3, 13, 3, 28)],
    )


def test_many_duplicate_field_arguments():
    expect_fails_rule(
        UniqueArgumentNames,
        """
    {
      field(arg1: "value", arg1: "value", arg1: "value")
    }
    """,
        [duplicate_arg("arg1", 3, 13, 3, 28), duplicate_arg("arg1", 3, 13, 3, 43)],
    )


def test_duplicate_directive_arguments():
    expect_fails_rule(
        UniqueArgumentNames,
        """
    {
      field @directive(arg1: "value", arg1: "value")
    }
    """,
        [duplicate_arg("arg1", 3, 24, 3, 39)],
    )


def test_many_duplicate_directive_arguments():
    expect_fails_rule(
        UniqueArgumentNames,
        """
    {
      field @directive(arg1: "value", arg1: "value", arg1: "value")
    }
    """,
        [duplicate_arg("arg1", 3, 24, 3, 39), duplicate_arg("arg1", 3, 24, 3, 54)],
    )
