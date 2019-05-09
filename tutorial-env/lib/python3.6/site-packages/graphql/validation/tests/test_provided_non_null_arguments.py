from graphql.language.location import SourceLocation
from graphql.validation.rules import ProvidedNonNullArguments

from .utils import expect_fails_rule, expect_passes_rule


def missing_field_arg(field_name, arg_name, type_name, line, column):
    return {
        "message": ProvidedNonNullArguments.missing_field_arg_message(
            field_name, arg_name, type_name
        ),
        "locations": [SourceLocation(line, column)],
    }


def missing_directive_arg(directive_name, arg_name, type_name, line, column):
    return {
        "message": ProvidedNonNullArguments.missing_directive_arg_message(
            directive_name, arg_name, type_name
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_ignores_unknown_arguments():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        dog {
          isHousetrained(unknownArgument: true)
        }
    }""",
    )


def test_arg_on_optional_arg():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        dog {
          isHousetrained(atOtherHomes: true)
        }
    }""",
    )


def test_no_arg_on_optional_arg():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        dog {
          isHousetrained
        }
    }""",
    )


def test_multiple_args():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleReqs(req1: 1, req2: 2)
        }
    }
    """,
    )


def test_multiple_args_reverse_order():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleReqs(req2: 2, req1: 1)
        }
    }
    """,
    )


def test_no_args_on_multiple_optional():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOpts
        }
    }
    """,
    )


def test_one_arg_on_multiple_optional():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOpts(opt1: 1)
        }
    }
    """,
    )


def test_second_arg_on_multiple_optional():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOpts(opt2: 1)
        }
    }
    """,
    )


def test_multiple_reqs_on_mixed_list():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOptAndReq(req1: 3, req2: 4)
        }
    }
    """,
    )


def test_multiple_reqs_and_one_opt_on_mixed_list():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOptAndReq(req1: 3, req2: 4, opt1: 5)
        }
    }
    """,
    )


def test_all_reqs_and_opts_on_mixed_list():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleOptAndReq(req1: 3, req2: 4, opt1: 5, opt2: 6)
        }
    }
    """,
    )


def test_missing_one_non_nullable_argument():
    expect_fails_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleReqs(req2: 2)
        }
    }
    """,
        [missing_field_arg("multipleReqs", "req1", "Int!", 4, 13)],
    )


def test_missing_multiple_non_nullable_arguments():
    expect_fails_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleReqs
        }
    }
    """,
        [
            missing_field_arg("multipleReqs", "req1", "Int!", 4, 13),
            missing_field_arg("multipleReqs", "req2", "Int!", 4, 13),
        ],
    )


def test_incorrect_value_and_missing_argument():
    expect_fails_rule(
        ProvidedNonNullArguments,
        """
    {
        complicatedArgs {
            multipleReqs(req1: "one")
        }
    }
    """,
        [missing_field_arg("multipleReqs", "req2", "Int!", 4, 13)],
    )


def test_ignore_unknown_directives():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        dog @unknown
    }
    """,
    )


def test_with_directives_of_valid_type():
    expect_passes_rule(
        ProvidedNonNullArguments,
        """
    {
        dog @include(if: true) {
            name
        }
        human @skip(if: false) {
            name
        }
    }
    """,
    )


def test_with_directive_with_missing_types():
    expect_fails_rule(
        ProvidedNonNullArguments,
        """
    {
        dog @include {
            name @skip
        }
    }
    """,
        [
            missing_directive_arg("include", "if", "Boolean!", 3, 13),
            missing_directive_arg("skip", "if", "Boolean!", 4, 18),
        ],
    )
