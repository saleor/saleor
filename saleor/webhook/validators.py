import re
from typing import Dict

from django.core.exceptions import ValidationError

HEADERS_NUMBER_LIMIT = 5
HEADERS_LENGTH_LIMIT = 78


def custom_headers_validator(headers) -> Dict[str, str]:
    """Validate headers in accordance with RFC5322.

    https://www.rfc-editor.org/rfc/rfc5322#section-2.2
    """
    if len(headers) > HEADERS_NUMBER_LIMIT:
        raise ValidationError(
            f"Number of headers exceeds the limit: {HEADERS_NUMBER_LIMIT}."
        )

    for k, v in headers.items():
        try:
            header = ": ".join([k, v])
        except TypeError:
            raise ValidationError("One of the header can't be converted to string.")

        if not header.isascii():
            raise ValidationError(f'"{header}" contains not valid ASCII character.')

        if len(header) > HEADERS_LENGTH_LIMIT:
            raise ValidationError(
                f'"{header}" exceeds the limit of characters: {HEADERS_LENGTH_LIMIT}.'
            )

        if not re.search(r"(^X-\S+)|(^Authorization\S+)", k):
            raise ValidationError(
                f'"{k}" does not match allowed key pattern: "X-*" or "Authorization*".'
            )

    return headers
