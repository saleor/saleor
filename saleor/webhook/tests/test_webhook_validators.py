import pytest
from django.core.exceptions import ValidationError

from ..validators import (
    HEADERS_LENGTH_LIMIT,
    HEADERS_NUMBER_LIMIT,
    custom_headers_validator,
)


@pytest.mark.parametrize(
    "headers,err_msg",
    [
        (
            {
                "Key1": "Value1",
                "Key2": "Value2",
                "Key3": "Value3",
                "Key4": "Value4",
                "Key5": "Value5",
                "Key6": "Value6",
            },
            f"Number of headers exceeds the limit: {HEADERS_NUMBER_LIMIT}.",
        ),
        (
            {"Key": "Value"},
            '"Key" does not match allowed key pattern: "X-*" or "Authorization*".',
        ),
        (
            {"X-Key": 123},
            "Header must consist of strings.",
        ),
        (
            {"Ke:y": "Value"},
            'Key "Ke:y" contains invalid character.',
        ),
        (
            {"Key": "Val:ue"},
            'Value "Val:ue" contains invalid character.',
        ),
        (
            {"Key": "X" * HEADERS_LENGTH_LIMIT},
            f'Header with key: "Key" exceeds the limit of characters: '
            f"{HEADERS_LENGTH_LIMIT}.",
        ),
        (
            {"ABCX-Key": "Value"},
            '"ABCX-Key" does not match allowed key pattern: "X-*" or "Authorization*".',
        ),
        (
            {"ABCAuthorization-Key": "Value"},
            '"ABCAuthorization-Key" does not match allowed key pattern:'
            ' "X-*" or "Authorization*".',
        ),
    ],
)
def test_webhook_validator(headers, err_msg):
    with pytest.raises(ValidationError) as err:
        custom_headers_validator(headers)
    assert err.value.message == err_msg
