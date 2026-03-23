import warnings
from typing import Any, overload

import nh3
from django.conf import settings
from django.core.exceptions import ValidationError
from urllib3.util import parse_url

from ..cleaners import URL_SCHEME_CLEANERS, URLCleanerError

ALLOWED_URL_SCHEMES = {
    # WARNING: do NOT add new schemes in directly to this list, only HTTP and HTTPS
    #          should be listed as they are cleaned by urllib3. Instead, add it to
    #          URL_SCHEME_CLEANERS and implement a cleaner that (at minimum) quotes
    #          special characters like "'<> and ASCII control characters
    #          (use urllib.util.parse.quote())
    "http",
    "https",
    *URL_SCHEME_CLEANERS.keys(),
}


def _clean_url_value(dirty_url: str | None) -> str:
    """Check if URL scheme is allowed."""
    if not dirty_url:
        return ""

    try:
        parsed_url = parse_url(dirty_url.strip())
    except ValueError:
        parsed_url = None

    if (
        parsed_url is None
        or parsed_url.scheme
        not in ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes
    ):
        warnings.warn(
            f"An invalid url or disallowed URL was sent: {dirty_url}",
            stacklevel=3,
        )
        return "#invalid"

    # If the scheme is HTTP(S), then urllib3 already took care of normalization
    # and thus quoted everything that should be quoted (such as dangerous characters
    # like `"`)
    # See https://github.com/urllib3/urllib3/blob/bd37a23af4552548f55d3c723fcb604f9a4983ca/src/urllib3/util/url.py#L415-L446
    if parsed_url.scheme in ("https", "http"):
        return parsed_url.url

    url_cleaner = URL_SCHEME_CLEANERS.get(parsed_url.scheme, None)

    if url_cleaner is None:
        if parsed_url.scheme in settings.HTML_CLEANER_PREFS.allowed_schemes:
            # Deprecated: this is only for backward compatibility - it doesn't define
            #             a cleaner which is dangerous.
            return dirty_url
        # NOTE: this exception should never happen unless a maintainer didn't read the
        #       comment in ALLOWED_URL_SCHEMES
        raise KeyError("No URL cleaner defined", parsed_url.scheme)

    try:
        return url_cleaner(dirty_url=dirty_url)
    except URLCleanerError as exc:
        # Note: InvalidUsage must NOT be handled (should return "Internal Error")
        #       it indicates a code bug if it's raised
        raise ValidationError(str(exc)) from exc
    except ValueError as exc:
        # Note: we do not do str(exc) as may reveal sensitive information
        raise ValidationError("Invalid URL") from exc


def _clean_meta_dict(value: dict) -> dict:
    if len(value) > 10:
        raise ValueError("Invalid meta block for EditorJS: too many fields")
    return value


def _clean_nested_list_items(items: Any, current_depth: int = 0) -> Any:
    """Validate the depth of nested EditorJS list isn't excessive.

    Important: this is a "before" pydantic validator, meaning types aren't checked
               yet as we want to run this validator early (instead of late).
    """
    if current_depth == settings.EDITOR_JS_LISTS_MAX_DEPTH:
        raise ValidationError("Invalid EditorJS list: maximum nesting level exceeded")

    # Type is invalid, skip it - we don't raise b/c pydantic will already take care
    # of that and will show a helpful error
    if not isinstance(items, list):
        return items

    for item in items:
        # Type is invalid, skip it (pydantic will take care of raising)
        if not isinstance(item, dict):
            continue
        if child_items := item.get("items"):
            _clean_nested_list_items(child_items, current_depth + 1)
    return items


@overload
def _clean_text(text: None) -> None: ...


@overload
def _clean_text(text: str) -> str: ...


def _clean_text(text: str | None) -> str | None:
    """Sanitize the text using nh3 to remove disallowed tags and attributes."""
    if not text:
        return text

    return nh3.clean(
        text,
        url_schemes=ALLOWED_URL_SCHEMES | settings.HTML_CLEANER_PREFS.allowed_schemes,
        attributes=settings.HTML_CLEANER_PREFS.allowed_attributes,
        tag_attribute_values=settings.HTML_CLEANER_PREFS.allowed_attribute_values,
        link_rel=settings.HTML_CLEANER_PREFS.link_rel,
    )
