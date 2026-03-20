import warnings

import pydantic_core
import pytest

from ...cleaners.html import HtmlCleanerSettings
from ...deprecations import SaleorDeprecationWarning

DIRTY = "<img src=x onerror=alert(1)>"
CLEAN = '<img src="x">'

XSS_URLS = [
    "javascript:prompt(1)",
    "javascript://alert(1)",
    "javascript://anything%0D%0A%0D%0Awindow.alert(1)",
    "javascript://%0Aalert(1)",
    "javascript:%0Aalert(1)",
    'vbscript:MsgBox("XSS")',
    "ftp://example.com",
    # HTML entities will be replaced by the browser to 'javascript:alert(1)'
    # in attributes (including `src="..."` and `href="..."`)
    "&#x6A;avascript&#0000058&#0000097lert(1)",
    "&#x6A;avascript:%20alert(1)",
]


@pytest.fixture
def cleaner_settings(settings):
    old_prefs = settings.HTML_CLEANER_PREFS

    # NOTE: use env vars to control the settings (using prefs.reload())
    #       to ensure the parsing logic of env var is tested
    #
    # Warnings need to be captured due to deprecation warnings for Saleor v3.23.0
    with warnings.catch_warnings(record=True, category=SaleorDeprecationWarning):
        prefs = HtmlCleanerSettings()
        settings.HTML_CLEANER_PREFS = prefs

        yield prefs
        settings.HTML_CLEANER_PREFS = old_prefs


@pytest.fixture
def no_link_rel(cleaner_settings):
    """Disable ``rel`` attribute for links.

    This disables appending `rel="noopener noreferrer"` to link which simplifies
    tests.
    """
    cleaner_settings.link_rel = None


def assert_pydantic_errors(
    exc: pydantic_core.ValidationError, expected_errors: list[dict]
) -> None:
    actual_errors = exc.errors()
    assert len(actual_errors) == len(expected_errors)
    for idx, err in enumerate(actual_errors):
        for k, v in expected_errors[idx].items():
            assert err[k] == v
