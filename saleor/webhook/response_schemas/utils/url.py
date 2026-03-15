import re
from typing import Annotated

from pydantic import AfterValidator, HttpUrl, TypeAdapter

# Matches a relative URL path starting with / that contains no whitespace.
RELATIVE_URL_PATTERN = re.compile(r"^/\S*$")

_http_url_adapter = TypeAdapter(HttpUrl)


def _validate_absolute_or_relative_url(value: str) -> str:
    if not value:
        return value
    if RELATIVE_URL_PATTERN.match(value):
        return value
    # Delegate to Pydantic HttpUrl for absolute URL validation.
    _http_url_adapter.validate_python(value)
    return str(value)


AbsoluteOrRelativeUrl = Annotated[str, AfterValidator(_validate_absolute_or_relative_url)]
