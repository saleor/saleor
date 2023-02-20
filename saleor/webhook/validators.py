from typing import Dict

from django.core.exceptions import ValidationError

HEADERS_NUMBER_LIMIT = 5
HEADERS_LENGTH_LIMIT = 998
KEY_CHARS_ALLOWED = (
    "!\"#$%&'()*+,-./0123456789;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
)
VALUE_CHARS_ALLOWED = (
    "!\"#$%&'()*+,-./0123456789;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~ \t"
)


def custom_headers_validator(headers: Dict[str, str]) -> Dict[str, str]:
    """Validate headers in accordance with RFC5322.

    https://www.rfc-editor.org/rfc/rfc5322#section-2.2
    """
    if len(headers) > HEADERS_NUMBER_LIMIT:
        raise ValidationError(
            f"Number of headers exceeds the limit: {HEADERS_NUMBER_LIMIT}."
        )

    for key, value in headers.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValidationError("Header must consist of strings.")

        if len(key) + len(value) + 2 > HEADERS_LENGTH_LIMIT:
            raise ValidationError(
                f'Header with key: "{key}" exceeds the limit of characters:'
                f" {HEADERS_LENGTH_LIMIT}."
            )

        if not set(key).issubset(set(KEY_CHARS_ALLOWED)):
            raise ValidationError(f'Key "{key}" contains invalid character.')

        if not set(value).issubset(set(VALUE_CHARS_ALLOWED)):
            raise ValidationError(f'Value "{value}" contains invalid character.')

        if not (
            key.lower().startswith("x-") or key.lower().startswith("authorization")
        ):
            raise ValidationError(
                f'"{key}" does not match allowed key pattern: '
                f'"X-*" or "Authorization*".'
            )

    return {k.lower(): v for k, v in headers.items()}
