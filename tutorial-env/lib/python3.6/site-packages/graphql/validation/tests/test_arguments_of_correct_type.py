from graphql.language.location import SourceLocation
from graphql.validation.rules import ArgumentsOfCorrectType

from .utils import expect_fails_rule, expect_passes_rule


def bad_value(arg_name, type_name, value, line, column, errors=None):
    if not errors:
        errors = [u'Expected type "{}", found {}.'.format(type_name, value)]

    return {
        "message": ArgumentsOfCorrectType.bad_value_message(
            arg_name, type_name, value, errors
        ),
        "locations": [SourceLocation(line, column)],
    }


# noinspection PyMethodMayBeStatic
class TestValidValues(object):
    def test_good_int_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: 2)
            }
        }
        """,
        )

    def test_good_boolean_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
              booleanArgField(booleanArg: true)
            }
        }
        """,
        )

    def test_good_string_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringArgField(stringArg: "foo")
            }
        }
        """,
        )

    def test_good_float_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                floatArgField(floatArg: 1.1)
            }
        }
        """,
        )

    def test_int_into_float(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                floatArgField(floatArg: 1)
            }
        }
        """,
        )

    def test_int_into_id(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
              idArgField(idArg: 1)
            }
        }
        """,
        )

    def test_string_into_id(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
              idArgField(idArg: "someIdString")
            }
        }
        """,
        )

    def test_good_enum_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: SIT)
            }
        }
        """,
        )


# noinspection PyMethodMayBeStatic
class TestInvalidStringValues(object):
    def test_int_into_string(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringArgField(stringArg: 1)
            }
        }
        """,
            [bad_value("stringArg", "String", "1", 4, 43)],
        )

    def test_float_into_string(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringArgField(stringArg: 1.0)
            }
        }
        """,
            [bad_value("stringArg", "String", "1.0", 4, 43)],
        )

    def test_bool_into_string(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringArgField(stringArg: true)
            }
        }
        """,
            [bad_value("stringArg", "String", "true", 4, 43)],
        )

    def test_unquoted_string_into_string(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringArgField(stringArg: BAR)
            }
        }
        """,
            [bad_value("stringArg", "String", "BAR", 4, 43)],
        )


# noinspection PyMethodMayBeStatic
class TestInvalidIntValues(object):
    def test_string_into_int(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: "3")
            }
        }
        """,
            [bad_value("intArg", "Int", '"3"', 4, 37)],
        )

    def test_big_int_into_int(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: 829384293849283498239482938)
            }
        }
        """,
            [bad_value("intArg", "Int", "829384293849283498239482938", 4, 37)],
        )

    def test_unquoted_string_into_int(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: FOO)
            }
        }
        """,
            [bad_value("intArg", "Int", "FOO", 4, 37)],
        )

    def test_simple_float_into_int(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: 3.0)
            }
        }
        """,
            [bad_value("intArg", "Int", "3.0", 4, 37)],
        )

    def test_float_into_int(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                intArgField(intArg: 3.333)
            }
        }
        """,
            [bad_value("intArg", "Int", "3.333", 4, 37)],
        )


# noinspection PyMethodMayBeStatic
class TestInvalidFloatValues(object):
    def test_string_into_float(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                floatArgField(floatArg: "3.333")
            }
        }
        """,
            [bad_value("floatArg", "Float", '"3.333"', 4, 41)],
        )

    def test_boolean_into_float(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                floatArgField(floatArg: true)
            }
        }
        """,
            [bad_value("floatArg", "Float", "true", 4, 41)],
        )

    def test_unquoted_into_float(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                floatArgField(floatArg: FOO)
            }
        }
        """,
            [bad_value("floatArg", "Float", "FOO", 4, 41)],
        )


# noinspection PyMethodMayBeStatic
class TestInvalidBooleanValues(object):
    def test_int_into_boolean(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                booleanArgField(booleanArg: 2)
            }
        }
        """,
            [bad_value("booleanArg", "Boolean", "2", 4, 45)],
        )

    def test_float_into_boolean(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                booleanArgField(booleanArg: 1.0)
            }
        }
        """,
            [bad_value("booleanArg", "Boolean", "1.0", 4, 45)],
        )

    def test_string_into_boolean(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                booleanArgField(booleanArg: "true")
            }
        }
        """,
            [bad_value("booleanArg", "Boolean", '"true"', 4, 45)],
        )

    def test_unquoted_into_boolean(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                booleanArgField(booleanArg: TRUE)
            }
        }
        """,
            [bad_value("booleanArg", "Boolean", "TRUE", 4, 45)],
        )


# noinspection PyMethodMayBeStatic
class TestInvalidIDValues(object):
    def test_float_into_id(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                idArgField(idArg: 1.0)
            }
        }
        """,
            [bad_value("idArg", "ID", "1.0", 4, 35)],
        )

    def test_boolean_into_id(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                idArgField(idArg: true)
            }
        }
        """,
            [bad_value("idArg", "ID", "true", 4, 35)],
        )

    def test_unquoted_into_id(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                idArgField(idArg: SOMETHING)
            }
        }
        """,
            [bad_value("idArg", "ID", "SOMETHING", 4, 35)],
        )


# noinspection PyMethodMayBeStatic
class TestInvalidEnumValues(object):
    def test_int_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: 2)
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", "2", 4, 45)],
        )

    def test_float_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: 1.0)
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", "1.0", 4, 45)],
        )

    def test_string_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: "SIT")
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", '"SIT"', 4, 45)],
        )

    def test_boolean_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: true)
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", "true", 4, 45)],
        )

    def test_unknown_enum_value_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: JUGGLE)
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", "JUGGLE", 4, 45)],
        )

    def test_different_case_enum_value_into_enum(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                doesKnowCommand(dogCommand: sit)
            }
        }
        """,
            [bad_value("dogCommand", "DogCommand", "sit", 4, 45)],
        )


# noinspection PyMethodMayBeStatic
class TestValidListValues(object):
    def test_good_list_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringListArgField(stringListArg: ["one", "two"])
            }
        }
        """,
        )

    def test_empty_list_value(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringListArgField(stringListArg: [])
            }
        }
        """,
        )

    def test_single_value_into_list(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringListArgField(stringListArg: "one")
            }
        }
        """,
        )


# noinspection PyMethodMayBeStatic
class TestInvalidListValues(object):
    def test_incorrect_item_type(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringListArgField(stringListArg: ["one", 2])
            }
        }
        """,
            [
                bad_value(
                    "stringListArg",
                    "String",
                    '["one", 2]',
                    4,
                    51,
                    ['In element #1: Expected type "String", found 2.'],
                )
            ],
        )

    def test_single_value_of_incorrect_type(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                stringListArgField(stringListArg: 1)
            }
        }
        """,
            [bad_value("stringListArg", "String", "1", 4, 51)],
        )


# noinspection PyMethodMayBeStatic
class TestValidNonNullableValues(object):
    def test_arg_on_optional_arg(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                isHousetrained(atOtherHomes: true)
            }
        }
        """,
        )

    def test_no_arg_on_optional_arg(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog {
                isHousetrained
            }
        }
        """,
        )

    def test_multiple_args(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleReqs(req1: 1, req2: 2)
            }
        }
        """,
        )

    def test_multiple_args_reverse_order(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleReqs(req2: 2, req1: 1)
            }
        }
        """,
        )

    def test_no_args_on_multiple_optional(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOpts
            }
        }
        """,
        )

    def test_one_arg_on_multiple_optional(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOpts(opt1: 1)
            }
        }
        """,
        )

    def test_second_arg_on_multiple_optional(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOpts(opt2: 1)
            }
        }
        """,
        )

    def test_multiple_reqs_and_one_opt_on_mixed_list(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOpts(req1: 3, req2: 4, opt1: 5)
            }
        }
        """,
        )

    def test_all_reqs_and_opts_on_mixed_list(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOpts(req1: 3, req2: 4, opt1: 5, opt2: 6)
            }
        }
        """,
        )


# noinspection PyMethodMayBeStatic
class TestInvalidNonNullableValues(object):
    def test_incorrect_value_type(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleOptsAndReq(req2: "two", req1: "one")
            }
        }
        """,
            [
                bad_value("req2", "Int", '"two"', 4, 42),
                bad_value("req1", "Int", '"one"', 4, 55),
            ],
        )

    def test_incorrect_value_and_missing_argument(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                multipleReqs(req1: "one")
            }
        }
        """,
            [bad_value("req1", "Int", '"one"', 4, 36)],
        )


# noinspection PyMethodMayBeStatic
class TestValidInputObjectValue(object):
    def test_optional_arg_despite_required_field_in_type(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField
            }
        }
        """,
        )

    def test_partial_object_only_required(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: { requiredField: true })
            }
        }
        """,
        )

    def test_partial_object_required_field_can_be_falsey(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: { requiredField: false })
            }
        }
        """,
        )

    def test_partial_object_including_required(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: { requiredField: false, intField: 4 })
            }
        }
        """,
        )

    def test_full_object(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: {
                    requiredField: true,
                    intField: 4,
                    stringField: "foo",
                    booleanField: false,
                    stringListField: ["one", "two"]
                })
            }
        }
        """,
        )

    def test_full_object_with_fields_in_different_order(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: {
                    stringListField: ["one", "two"]
                    booleanField: false,
                    requiredField: true,
                    stringField: "foo",
                    intField: 4,
                })
            }
        }
        """,
        )


# noinspection PyMethodMayBeStatic
class TestInvalidInputObjectValue(object):
    def test_partial_object_missing_required(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: { intField: 4 })
            }
        }
        """,
            [
                bad_value(
                    "complexArg",
                    "ComplexInput",
                    "{intField: 4}",
                    4,
                    45,
                    ['In field "requiredField": Expected "Boolean!", found null.'],
                )
            ],
        )

    def test_partial_object_invalid_field_type(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: {
                    stringListField: ["one", 2],
                    requiredField: true
                })
            }
        }
        """,
            [
                bad_value(
                    "complexArg",
                    "ComplexInput",
                    '{stringListField: ["one", 2], requiredField: true}',
                    4,
                    45,
                    [
                        'In field "stringListField": In element #1: Expected type "String", found 2.'
                    ],
                )
            ],
        )

    def test_partial_object_unknown_field_arg(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            complicatedArgs {
                complexArgField(complexArg: {
                    requiredField: true
                    unknownField: "value",
                })
            }
        }
        """,
            [
                bad_value(
                    "complexArg",
                    "ComplexInput",
                    '{requiredField: true, unknownField: "value"}',
                    4,
                    45,
                    ['In field "unknownField": Unknown field.'],
                )
            ],
        )


# noinspection PyMethodMayBeStatic
class TestDirectiveArguments(object):
    def test_with_directives_of_valid_types(self):
        expect_passes_rule(
            ArgumentsOfCorrectType,
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

    def test_with_directive_with_incorrect_types(self):
        expect_fails_rule(
            ArgumentsOfCorrectType,
            """
        {
            dog @include(if: "yes") {
                name @skip(if: ENUM)
            }
        }
        """,
            [
                bad_value("if", "Boolean", '"yes"', 3, 30),
                bad_value("if", "Boolean", "ENUM", 4, 32),
            ],
        )
