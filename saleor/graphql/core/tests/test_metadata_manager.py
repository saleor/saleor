from django.core.exceptions import ValidationError
from sympy.testing.pytest import raises

from saleor.core.models import ModelWithMetadata
from saleor.graphql.core.utils.metadata_manager import (
    metadata_contains_empty_key,
    update_metadata_on_instance,
    validate_metadata_keys_and_throw,
)


def test_metadata_contains_empty_key():
    valid_list = [{"key": "valid", "value": "value"}]

    invalid_list = [{"key": "", "value": "value"}]
    invalid_list_with_one_valid = [
        {"key": "", "value": "value"},
        {"key": "foo", "value": "value"},
    ]

    assert metadata_contains_empty_key(invalid_list) is True
    assert metadata_contains_empty_key(invalid_list_with_one_valid) is True
    assert metadata_contains_empty_key(valid_list) is False


def test_validate_metadata_keys_and_throw():
    invalid_list_with_one_valid = [
        {"key": "", "value": "value"},
        {"key": "foo", "value": "value"},
    ]

    with raises(ValidationError):
        validate_metadata_keys_and_throw(invalid_list_with_one_valid)


def test_validate_metadata_keys_and_throw_valid_list():
    valid_list = [{"key": "valid", "value": "value"}]

    validate_metadata_keys_and_throw(valid_list)


def test_update_metadata_on_instance():
    valid_list = [{"key": "valid", "value": "value"}]

    class TestInstance(ModelWithMetadata):
        pass

    test_instance = TestInstance()

    update_metadata_on_instance(
        instance=test_instance, metadata=valid_list, private_metadata=valid_list
    )

    assert test_instance.metadata == {"valid": "value"}
    assert test_instance.private_metadata == {"valid": "value"}
