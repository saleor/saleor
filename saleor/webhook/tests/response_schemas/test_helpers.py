from pydantic import BaseModel, ValidationError

from ...response_schemas.utils.helpers import parse_validation_error


class ExampleSchema(BaseModel):
    field1: int
    field2: str


def test_parse_validation_error_single_error():
    # given
    invalid_data = {"field1": "not_an_int", "field2": "valid_string"}

    # when
    try:
        ExampleSchema.model_validate(invalid_data)
    except ValidationError as error:
        error_msg = parse_validation_error(error)

    # then
    assert error_msg == (
        f"Incorrect value ({invalid_data['field1']}) for field: field1. Error: Input should be a valid integer, unable to parse string as an integer."
    )


def test_parse_validation_error_multiple_errors():
    # given
    invalid_data = {"field1": "not_an_int", "field2": 123}

    # when
    try:
        ExampleSchema.model_validate(invalid_data)
    except ValidationError as error:
        error_msg = parse_validation_error(error)

    # then
    assert error_msg == (
        f"Incorrect value ({invalid_data['field1']}) for field: field1. Error: Input should be a valid integer, unable to parse string as an integer.\n\n"
        f"Incorrect value ({invalid_data['field2']}) for field: field2. Error: Input should be a valid string."
    )


def test_parse_validation_error_missing_field_value():
    # given
    invalid_data = {"field1": 1232}

    # when
    try:
        ExampleSchema.model_validate(invalid_data)
    except ValidationError as error:
        error_msg = parse_validation_error(error)

    # then
    assert error_msg == f"Missing value for field: field2. Input: {invalid_data}."
