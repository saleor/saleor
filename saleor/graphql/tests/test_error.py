from typing import Annotated

import pytest
from pydantic import BaseModel, Field, StringConstraints, field_validator
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import PydanticCustomError

from ..error import pydantic_to_validation_error


class SampleModel(BaseModel):
    name: Annotated[str, StringConstraints(min_length=3)]
    age: Annotated[int, Field(ge=0)]


class ModelWithCustomErrorCode(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise PydanticCustomError(
                "invalid_url_format",
                "Enter a valid URL.",
                {"error_code": "invalid_url_format"},
            )
        return v


def test_pydantic_to_validation_error_single_field():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        SampleModel(name="ab", age=5)

    # when
    error = pydantic_to_validation_error(exc_info.value)

    # then
    assert error.message_dict == {
        "name": ["String should have at least 3 characters"],
    }
    assert error.error_dict["name"][0].code == "invalid"


def test_pydantic_to_validation_error_multiple_fields():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        SampleModel(name="ab", age=-1)

    # when
    error = pydantic_to_validation_error(exc_info.value)

    # then
    assert error.message_dict == {
        "name": ["String should have at least 3 characters"],
        "age": ["Input should be greater than or equal to 0"],
    }
    assert error.error_dict["name"][0].code == "invalid"
    assert error.error_dict["age"][0].code == "invalid"


def test_pydantic_to_validation_error_uses_default_error_code():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        SampleModel(name="ab", age=5)

    # when
    error = pydantic_to_validation_error(exc_info.value)

    # then
    assert error.message_dict == {
        "name": ["String should have at least 3 characters"],
    }
    assert error.error_dict["name"][0].code == "invalid"


def test_pydantic_to_validation_error_uses_custom_error_code():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        SampleModel(name="ab", age=5)

    # when
    error = pydantic_to_validation_error(
        exc_info.value, default_error_code="custom_code"
    )

    # then
    assert error.message_dict == {
        "name": ["String should have at least 3 characters"],
    }
    assert error.error_dict["name"][0].code == "custom_code"


def test_pydantic_to_validation_error_per_error_code_overrides_global():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        ModelWithCustomErrorCode(url="http://not-https.com")

    # when
    # Global fallback is "invalid", but the validator embeds "invalid_url_format"
    error = pydantic_to_validation_error(exc_info.value, default_error_code="invalid")

    # then
    assert error.message_dict == {"url": ["Enter a valid URL."]}
    assert error.error_dict["url"][0].code == "invalid_url_format"


def test_pydantic_to_validation_error_falls_back_to_global_when_no_ctx_code():
    # given
    with pytest.raises(PydanticValidationError) as exc_info:
        SampleModel(name="ab", age=5)

    # when
    # Built-in constraint (min_length) carries no error_code in ctx
    error = pydantic_to_validation_error(
        exc_info.value, default_error_code="fallback_code"
    )

    # then
    assert error.error_dict["name"][0].code == "fallback_code"
