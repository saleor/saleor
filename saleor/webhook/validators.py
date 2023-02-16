import re
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
        try:
            header = ": ".join([key, value])
        except TypeError:
            raise ValidationError(f'Header with "{key}" can\'t be converted to string.')

        if len(header) > HEADERS_LENGTH_LIMIT:
            raise ValidationError(
                f'"{header}" exceeds the limit of characters: {HEADERS_LENGTH_LIMIT}.'
            )

        if not set(key).issubset(set(KEY_CHARS_ALLOWED)):
            raise ValidationError(f'Key "{key}" contains invalid character.')

        if not set(value).issubset(set(VALUE_CHARS_ALLOWED)):
            raise ValidationError(f'Value "{value}" contains invalid character.')

        if not re.search(r"(^X-\S*)|(^Authorization\S*)", key):
            raise ValidationError(
                f'"{key}" does not match allowed key pattern: '
                f'"X-*" or "Authorization*".'
            )

    return headers
