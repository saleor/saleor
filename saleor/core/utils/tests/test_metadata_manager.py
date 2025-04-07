import pytest

from ..metadata_manager import metadata_is_valid


@pytest.mark.parametrize(
    "metadata",
    [
        {"key1": "value1", "key2": "value2"},
        {},
        {"key1": ""},
    ],
)
def test_metadata_is_valid_true(metadata):
    # when
    is_metadata_valid = metadata_is_valid(metadata)

    # then
    assert is_metadata_valid is True


@pytest.mark.parametrize(
    "metadata",
    [
        None,
        "not_a_dict",
        {"key1": 123},
        {123: "value1"},
        {"": "value1"},
        {"   ": "value1"},
    ],
)
def test_metadata_is_valid_false(metadata):
    # when
    is_metadata_valid = metadata_is_valid(metadata)

    # then
    assert is_metadata_valid is False
