import warnings

import pytest
from django.core.exceptions import ValidationError

from .. import clean_editorjs
from ..cleaners import _clean_url_value
from .conftest import XSS_URLS


@pytest.mark.parametrize(
    ("input_url", "expected_cleaned_url", "is_allowed"),
    # Invalid cases
    [(url, "#invalid", False) for url in XSS_URLS]
    + [
        # Valid cases
        ("https://example.com", "https://example.com", True),
        ("http://example.com", "http://example.com", True),
        # We shouldn't trust anything in the URL, quote everything
        ('https://example.com?x="', "https://example.com?x=%22", True),
        ('https://example.com/"', "https://example.com/%22", True),
        # Special characters must be encoded
        ('https://example.com/path"?x="', "https://example.com/path%22?x=%22", True),
        ('https://example.com#"<>', "https://example.com#%22%3C%3E", True),
        ("https://example.com/\x00", "https://example.com/%00", True),
        ("https://example.com/\nonerror=1", "https://example.com/%0Aonerror=1", True),
        ("https://exampleß.test/", "https://xn--example-6va.test/", True),
        # Tel and mailto should be cleaned
        ('tel:">', "tel:%22%3E", True),
        ('mailto:?body=">', "mailto:?body=%22%3E", True),
    ],
)
def test_clean_url(input_url, expected_cleaned_url, is_allowed):
    with warnings.catch_warnings(record=True) as warns:
        actual = _clean_url_value(input_url)

        expected_warning_count = 0 if is_allowed else 1
        assert len(warns) == expected_warning_count

    assert actual == expected_cleaned_url


@pytest.mark.parametrize(
    ("input_url", "expected_error"),
    [
        ("mailto:joe@[1]", "Invalid IPv6 address"),
        (
            "mailto:joe@example.com?1" + "&".join(f"{i}={i}" for i in range(11)),
            # Actual error is from urllib: "ValueError: Max number of fields exceeded"
            "Invalid URL",
        ),
    ],
)
def test_clean_url_error_handling(input_url: str, expected_error: str):
    with pytest.raises(ValidationError, match=expected_error):
        _clean_url_value(input_url)


def test_clean_url_allows_custom_allow_list(monkeypatch, cleaner_settings):
    """Ensure that we allow to override the settings to add more allowed URL schemes.

    This is a backward compatibility check, it will be removed in 3.23.0.
    """

    url = "non-default:foo"

    # Should refuse the URL scheme if it's not allowed
    with warnings.catch_warnings(record=True):
        assert _clean_url_value(url) == "#invalid"

    # Catches warnings due to deprecation notices from Saleor (v3.23.0)
    with warnings.catch_warnings(record=True):
        monkeypatch.setenv("UNSAFE_EDITOR_JS_ALLOWED_URL_SCHEMES", "non-default,other")
        cleaner_settings.reload()

    # When allowed it should allow the use of that URL scheme even if a cleaner
    # isn't defined.
    assert _clean_url_value(url) == url
    assert _clean_url_value("other:") == "other:"
    with warnings.catch_warnings(record=True):
        assert _clean_url_value("not-ok:") == "#invalid"


def test_clean_editor_js_invalid_url():
    # given
    url_invalid = "javascript:alert('Saleor')"
    url_valid = "https://github.com/editor-js"
    text = (
        'The Saleor Winter Sale is snowed under with seasonal offers. <a href="{}"> '
        "Unreal products at unreal prices. Literally, they are not real products, "
        "but the Saleor demo store is a genuine e-commerce leader. "
        'Check this out: <a href="{}">'
    )

    data = {
        "blocks": [
            {"data": {"text": text.format(url_invalid, url_valid)}, "type": "paragraph"}
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    cleaned_text = result["blocks"][0]["data"]["text"]
    assert "javascript:" not in cleaned_text
    assert url_valid in cleaned_text
    assert "The Saleor Winter Sale" in cleaned_text


def test_clean_editor_js_image_invalid_url():
    # given
    url = "javascript:alert('XSS')"
    data = {"blocks": [{"type": "image", "data": {"file": {"url": url}}}]}

    # when
    with warnings.catch_warnings(record=True) as warns:
        result = clean_editorjs(data, for_django=False)

        assert len(warns) == 1
        assert "disallowed URL was sent" in str(warns[0].message)

    # then
    assert result["blocks"][0]["data"]["file"]["url"] == "#invalid"


def test_clean_editor_js_image_disallowed_scheme():
    # given
    url = "ftp://example.com/image.png"
    data = {"blocks": [{"type": "image", "data": {"file": {"url": url}}}]}

    # when
    with warnings.catch_warnings(record=True) as warns:
        result = clean_editorjs(data, for_django=False)

        assert len(warns) == 1
        assert "disallowed URL was sent" in str(warns[0].message)

    # then
    assert result["blocks"][0]["data"]["file"]["url"] == "#invalid"
