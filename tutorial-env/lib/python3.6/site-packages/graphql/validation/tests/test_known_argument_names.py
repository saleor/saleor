from graphql.language.location import SourceLocation
from graphql.validation.rules.known_argument_names import (
    KnownArgumentNames,
    _unknown_arg_message,
    _unknown_directive_arg_message,
)

from .utils import expect_fails_rule, expect_passes_rule


def unknown_arg(arg_name, field_name, type_name, suggested_args, line, column):
    return {
        "message": _unknown_arg_message(
            arg_name, field_name, type_name, suggested_args
        ),
        "locations": [SourceLocation(line, column)],
    }


def unknown_directive_arg(arg_name, directive_name, suggested_args, line, column):
    return {
        "message": _unknown_directive_arg_message(
            arg_name, directive_name, suggested_args
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_single_arg_is_known():
    expect_passes_rule(
        KnownArgumentNames,
        """
        fragment argOnRequiredArg on Dog {
          doesKnowCommand(dogCommand: SIT)
        }
    """,
    )


def test_multiple_args_are_known():
    expect_passes_rule(
        KnownArgumentNames,
        """
      fragment multipleArgs on ComplicatedArgs {
        multipleReqs(req1: 1, req2: 2)
      }
    """,
    )


def test_ignore_args_of_unknown_fields():
    expect_passes_rule(
        KnownArgumentNames,
        """
      fragment argOnUnknownField on Dog {
        unknownField(unknownArg: SIT)
      }
    """,
    )


def test_multiple_args_in_reverse_order_are_known():
    expect_passes_rule(
        KnownArgumentNames,
        """
      fragment multipleArgsReverseOrder on ComplicatedArgs {
        multipleReqs(req2: 2, req1: 1)
      }
    """,
    )


def test_no_args_on_optional_arg():
    expect_passes_rule(
        KnownArgumentNames,
        """
      fragment noArgOnOptionalArg on Dog {
        isHousetrained
      }
    """,
    )


def test_args_are_known_deeply():
    expect_passes_rule(
        KnownArgumentNames,
        """
      {
        dog {
          doesKnowCommand(dogCommand: SIT)
        }
        human {
          pet {
            ... on Dog {
                doesKnowCommand(dogCommand: SIT)
            }
          }
        }
      }
    """,
    )


def test_directive_args_are_known():
    expect_passes_rule(
        KnownArgumentNames,
        """
      {
        dog @skip(if: true)
      }
    """,
    )


def test_undirective_args_are_invalid():
    expect_fails_rule(
        KnownArgumentNames,
        """
      {
        dog @skip(unless: true)
      }
    """,
        [unknown_directive_arg("unless", "skip", [], 3, 19)],
    )


def test_invalid_arg_name():
    expect_fails_rule(
        KnownArgumentNames,
        """
      fragment invalidArgName on Dog {
        doesKnowCommand(unknown: true)
      }
    """,
        [unknown_arg("unknown", "doesKnowCommand", "Dog", [], 3, 25)],
    )


def test_unknown_args_amongst_known_args():
    expect_fails_rule(
        KnownArgumentNames,
        """
      fragment oneGoodArgOneInvalidArg on Dog {
        doesKnowCommand(whoknows: 1, dogCommand: SIT, unknown: true)
      }
    """,
        [
            unknown_arg("whoknows", "doesKnowCommand", "Dog", [], 3, 25),
            unknown_arg("unknown", "doesKnowCommand", "Dog", [], 3, 55),
        ],
    )


def test_unknown_args_deeply():
    expect_fails_rule(
        KnownArgumentNames,
        """
      {
        dog {
          doesKnowCommand(unknown: true)
        }
        human {
          pet {
            ... on Dog {
              doesKnowCommand(unknown: true)
            }
          }
        }
      }
    """,
        [
            unknown_arg("unknown", "doesKnowCommand", "Dog", [], 4, 27),
            unknown_arg("unknown", "doesKnowCommand", "Dog", [], 9, 31),
        ],
    )
