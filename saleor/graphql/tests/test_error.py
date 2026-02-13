from typing import Annotated

import pytest
from pydantic import BaseModel, Field, StringConstraints
from pydantic import ValidationError as PydanticValidationError

from ..error import pydantic_to_validation_error


class SampleModel(BaseModel):
    name: Annotated[str, StringConstraints(min_length=3)]
    age: Annotated[int, Field(ge=0)]


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
    error = pydantic_to_validation_error(exc_info.value, error_code="custom_code")

    # then
    assert error.message_dict == {
        "name": ["String should have at least 3 characters"],
    }
    assert error.error_dict["name"][0].code == "custom_code"
