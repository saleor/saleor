import re
from typing import Dict

from django.core.exceptions import ValidationError

HEADERS_NUMBER_LIMIT = 5
HEADERS_LENGTH_LIMIT = 78


def custom_headers_validator(headers: Dict[str, str]) -> Dict[str, str]:
    """Validate headers in accordance with RFC5322.

    https://www.rfc-editor.org/rfc/rfc5322#section-2.2
    """
    if len(headers) > HEADERS_NUMBER_LIMIT:
        raise ValidationError(
            f"Number of headers exceeds the limit: {HEADERS_NUMBER_LIMIT}."
        )

    key_chars_allowed = "".join([chr(i) for i in range(33, 127) if i != ord(":")])
    value_chars_allowed = key_chars_allowed + chr(32) + chr(9)

    for key, value in headers.items():
        try:
            header = ": ".join([key, value])
        except TypeError:
            raise ValidationError(f'Header with "{key}" can\'t be converted to string.')

        if not set(key).issubset(set(key_chars_allowed)):
            raise ValidationError(f'Key "{key}" contains invalid character.')

        if not set(value).issubset(set(value_chars_allowed)):
            raise ValidationError(f'Value "{value}" contains invalid character.')

        if len(header) > HEADERS_LENGTH_LIMIT:
            raise ValidationError(
                f'"{header}" exceeds the limit of characters: {HEADERS_LENGTH_LIMIT}.'
            )

        if not re.search(r"(^X-\S+)|(^Authorization\S+)", key):
            raise ValidationError(
                f'"{key}" does not match allowed key pattern: '
                f'"X-*" or "Authorization*".'
            )

    return headers
