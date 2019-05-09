from graphql.language.location import SourceLocation
from graphql.validation.rules import DefaultValuesOfCorrectType

from .utils import expect_fails_rule, expect_passes_rule


def default_for_non_null_arg(var_name, type_name, guess_type_name, line, column):
    return {
        "message": DefaultValuesOfCorrectType.default_for_non_null_arg_message(
            var_name, type_name, guess_type_name
        ),
        "locations": [SourceLocation(line, column)],
    }


def bad_value(var_name, type_name, value, line, column, errors=None):
    if not errors:
        errors = ['Expected type "{}", found {}.'.format(type_name, value)]

    return {
        "message": DefaultValuesOfCorrectType.bad_value_for_default_arg_message(
            var_name, type_name, value, errors
        ),
        "locations": [SourceLocation(line, column)],
    }


def test_variables_with_no_default_values():
    return expect_passes_rule(
        DefaultValuesOfCorrectType,
        """
    query NullableValues($a: Int, $b: String, $c: ComplexInput) {
        dog { name }
    }
    """,
    )


def test_required_variables_without_default_values():
    expect_passes_rule(
        DefaultValuesOfCorrectType,
        """
    query RequiredValues($a: Int!, $b: String!) {
        dog { name }
    }
    """,
    )


def test_variables_with_valid_default_values():
    expect_passes_rule(
        DefaultValuesOfCorrectType,
        """
    query WithDefaultValues(
        $a: Int = 1,
        $b: String = "ok",
        $c: ComplexInput = { requiredField: true, intField: 3 }
    ) {
        dog { name }
    }
    """,
    )


def test_no_required_variables_with_default_values():
    expect_fails_rule(
        DefaultValuesOfCorrectType,
        """
    query UnreachableDefaultValues($a: Int! = 3, $b: String! = "default") {
        dog { name }
    }
    """,
        [
            default_for_non_null_arg("a", "Int!", "Int", 2, 47),
            default_for_non_null_arg("b", "String!", "String", 2, 64),
        ],
    )


def test_variables_with_invalid_default_values():
    expect_fails_rule(
        DefaultValuesOfCorrectType,
        """
    query InvalidDefaultValues(
        $a: Int = "one",
        $b: String = 4,
        $c: ComplexInput = "notverycomplex"
    ) {
        dog { name }
    }
    """,
        [
            bad_value("a", "Int", '"one"', 3, 19),
            bad_value("b", "String", "4", 4, 22),
            bad_value(
                "c",
                "ComplexInput",
                '"notverycomplex"',
                5,
                28,
                ['Expected "ComplexInput", found not an object.'],
            ),
        ],
    )


def test_variables_missing_required_field():
    expect_fails_rule(
        DefaultValuesOfCorrectType,
        """
    query MissingRequiredField($a: ComplexInput = {intField: 3}) {
        dog { name }
    }
    """,
        [
            bad_value(
                "a",
                "ComplexInput",
                "{intField: 3}",
                2,
                51,
                ['In field "requiredField": Expected "Boolean!", found null.'],
            )
        ],
    )


def test_list_variables_with_invalid_item():
    expect_fails_rule(
        DefaultValuesOfCorrectType,
        """
    query invalidItem($a: [String] = ["one", 2]) {
        dog { name }
    }
    """,
        [
            bad_value(
                "a",
                "[String]",
                '["one", 2]',
                2,
                38,
                ['In element #1: Expected type "String", found 2.'],
            )
        ],
    )
