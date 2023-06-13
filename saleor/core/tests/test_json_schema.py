import json
from enum import Enum
from typing import Annotated, Optional

import pytest
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import Field, validator

from ..json_schema import (
    CustomValueError,
    ErrorConversionConfig,
    ErrorConversionModel,
    to_camel,
)


@pytest.mark.parametrize(
    "snake_str,camel_str", [("long_field_name", "longFieldName"), ("field", "field")]
)
def test_to_camel(snake_str, camel_str):
    assert to_camel(snake_str) == camel_str


@pytest.mark.parametrize(
    "message,expected", [("", ""), ("some error message", "Some error message.")]
)
def test_normalize_error_message(message, expected):
    assert ErrorConversionModel.normalize_error_message(message) == expected


class ErrorCode(Enum):
    DEFAULT = "default"
    CLASS = "class"
    SUBCLASS = "sub_class"
    FIELD = "field"
    SUBCLASS_FIELD = "sub_class_field"
    CUSTOM_VALUE_ERROR = "custom_value_error"


class SubConversionModel(ErrorConversionModel):
    data_a: Annotated[str, Field(min_length=1)]
    data_b: Annotated[str, Field(min_length=1)]
    data_c: Annotated[str, Field(min_length=1)]
    data_d: Optional[str] = None

    class Config(ErrorConversionConfig):
        default_error_override = ErrorCode.SUBCLASS
        error_type_overrides = {
            "value_error.missing": {
                "code": ErrorCode.SUBCLASS,
                "msg": "subclass mapping",
            }
        }
        field_error_overrides = {
            "data_c": {
                "code": ErrorCode.SUBCLASS_FIELD,
                "msg": "subclass field mapping",
            }
        }

    @validator("data_d", always=True)
    def validate_data(cls, val):
        raise CustomValueError(
            "custom value error", error_code=ErrorCode.CUSTOM_VALUE_ERROR
        )


class ConversionModel(ErrorConversionModel):
    data_a: Annotated[str, Field(min_length=1)]
    data_b: Annotated[Optional[str], Field(min_length=1)] = None
    data_c: Optional[str] = None
    sub_schema: Optional[SubConversionModel] = None

    class Config(ErrorConversionConfig):
        default_error_override = {"code": ErrorCode.DEFAULT, "msg": "default mapping"}
        error_type_overrides = {
            "value_error.missing": {"code": ErrorCode.CLASS, "msg": "class mapping"}
        }
        field_error_overrides = {
            "data_b": {
                "code": ErrorCode.FIELD,
                "msg": "field mapping",
            }
        }

    @validator("data_c")
    def validate_data(cls, val):
        raise CustomValueError(
            "custom value error", error_code=ErrorCode.CUSTOM_VALUE_ERROR
        )


@pytest.mark.parametrize(
    "field_name,error_field",
    [(None, NON_FIELD_ERRORS), ("field_name", "field_name")],
)
def test_root_validation_error(field_name, error_field):
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw("invalid format", field_name=field_name)
    # then
    assert len(error.value.error_dict[error_field]) == 1
    validation_error = error.value.error_dict[error_field][0]
    assert validation_error.code == ErrorCode.DEFAULT.value
    assert validation_error.message == "Default mapping."


def test_default_error_mapping():
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw(json.dumps({"dataA": ""}))
    # then
    validation_error = error.value.error_dict["dataA"][0]
    assert validation_error.code == ErrorCode.DEFAULT.value
    assert validation_error.message == "Default mapping."


def test_error_mapping():
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw(json.dumps({}))
    # then
    validation_error = error.value.error_dict["dataA"][0]
    assert validation_error.code == ErrorCode.CLASS.value
    assert validation_error.message == "Class mapping."


def test_field_error_mapping():
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw(json.dumps({"dataB": ""}))
    # then
    validation_error = error.value.error_dict["dataB"][0]
    assert validation_error.code == ErrorCode.FIELD.value
    assert validation_error.message == "Field mapping."


def test_custom_value_error_mapping():
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw(json.dumps({"dataC": ""}))
    validation_error = error.value.error_dict["dataC"][0]
    assert validation_error.code == ErrorCode.CUSTOM_VALUE_ERROR.value
    assert validation_error.message == "Custom value error."


def test_error_mapping_with_sub_schema():
    # when
    with pytest.raises(DjangoValidationError) as error:
        ConversionModel.parse_raw(json.dumps({"subSchema": {"dataA": "", "dataC": ""}}))

    # Default error mapping from Schema not SubSchema is used
    validation_error = error.value.error_dict["subSchema.dataA"][0]
    assert validation_error.code == ErrorCode.DEFAULT.value
    assert validation_error.message == "Default mapping."

    validation_error = error.value.error_dict["subSchema.dataB"][0]
    assert validation_error.code == ErrorCode.CLASS.value
    assert validation_error.message == "Class mapping."

    validation_error = error.value.error_dict["subSchema.dataC"][0]
    assert validation_error.code == ErrorCode.SUBCLASS_FIELD.value
    assert validation_error.message == "Subclass field mapping."

    validation_error = error.value.error_dict["subSchema.dataD"][0]
    assert validation_error.code == ErrorCode.CUSTOM_VALUE_ERROR.value
    assert validation_error.message == "Custom value error."
