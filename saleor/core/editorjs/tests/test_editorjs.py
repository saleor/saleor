import json
import warnings
from copy import deepcopy

import django.core.exceptions
import pydantic_core
import pytest
from django.utils.html import strip_tags

from ...cleaners.html import HtmlCleanerSettings
from ...deprecations import SaleorDeprecationWarning
from .. import clean_editorjs, editorjs_to_text
from ..cleaners import _clean_url_value
from .conftest import assert_pydantic_errors

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


def assert_paragraph_cleaned(text_input: str, expected_text_output: str) -> None:
    input = {"blocks": [{"type": "paragraph", "data": {"text": text_input}}]}
    expected = {
        "blocks": [{"type": "paragraph", "data": {"text": expected_text_output}}]
    }

    actual = clean_editorjs(input, for_django=False)
    assert actual == expected


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
    with pytest.raises(django.core.exceptions.ValidationError, match=expected_error):
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


@pytest.mark.parametrize(
    ("_case", "text", "expected_cleaned_text"),
    [
        # Invalid URLs
        (
            f"XSS URL: {url}",
            f'<a href="{url}">link</a>',
            '<a rel="noopener noreferrer">link</a>',
        )
        for url in XSS_URLS
    ]
    + [
        (
            "SVG should be fully deleted",
            (
                "<p>My SVG:</p>"
                # Safe SVG (draws a rectangle) but we expect nh3 to not try clean inside
                # the SVG body instead it should drop the whole block.
                # SVG is fairly complex to parse and thus <img> should be used instead
                # when dealing with untrusted data as it already removes all scripts
                # that could running within an SVG file.
                '<svg width="300" height="130" xmlns="http://www.w3.org/2000/svg">'
                '<rect width="100" height="100" />'
                "</svg>"
            ),
            "<p>My SVG:</p>",  # we expect the <svg> to be deleted
        ),
        (
            "Script blocks should be deleted",
            "<script>alert(1)</script>",
            "",
        ),
        (
            # '<style>' is an XSS vector and poses other security risks
            "Style blocks should be deleted",
            "<style>a {color: red}</style>",
            "",
        ),
        (
            # 'style' attribute is an XSS vector and poses other security risks
            "Style attributes should be deleted",
            '<span style="color: red">text</span>',
            "<span>text</span>",
        ),
        (
            "Common XSS Bypass: Backticks",
            "<img src=javascript:alert(1)>",
            "<img>",
        ),
        ("VBScript", "<img src='vbscript:msgbox(1)'>", "<img>"),
        ("Slash Delimer", "<img/onload=alert(1)>", "<img>"),
        (
            "Body Image",
            "<body background='javascript:alert(1)'>",
            "",
        ),
        ("SVG attributes are removed", "<svg/onload=alert('XSS')>", ""),
        (
            "Unsupported URL schemes are dropped",
            '<a href="wss://foo.test">link</a>',
            '<a rel="noopener noreferrer">link</a>',
        ),
        (
            "Supported URL schemes are kept",
            '<a href="https://foo.test">link</a>',
            '<a href="https://foo.test" rel="noopener noreferrer">link</a>',
        ),
        (
            # Will be denied in a future Saleor release due to being unsupported
            # by nh3 currently
            "Relative URLs are allowed",
            '<a href="example-relative-url">link</a>',
            '<a href="example-relative-url" rel="noopener noreferrer">link</a>',
        ),
    ],
)
def test_clean_text_data_block(_case: str, text: str, expected_cleaned_text: str):
    assert_paragraph_cleaned(text, expected_cleaned_text)


@pytest.mark.parametrize(
    ("_case", "allowed_attributes", "html_input", "expected_output"),
    [
        (
            "a[is] is allowed => shouldn't drop 'is' attr",
            {"a": ["is"]},
            '<a href="https://example.com" is="dummy">Link</a>',
            '<a href="https://example.com" is="dummy">Link</a>',
        ),
        (
            "a[is] is allowed only on <a> => MUST drop 'is' attr on <div>",
            {"a": ["is"]},
            '<div is="dummy">x</div>',
            "<div>x</div>",
        ),
        (
            "a[foo] is NOT allowed => MUST drop 'foo'",
            {"a": ["is"]},
            '<a href="https://example.com" is="dummy" foo="bar">Link</a>',
            '<a href="https://example.com" is="dummy">Link</a>',
        ),
    ],
)
def test_clean_text_data_block_allow_custom_attributes(
    monkeypatch,
    cleaner_settings,
    _case: str,
    allowed_attributes: dict[str, list[str]],
    html_input: str,
    expected_output: str,
):
    monkeypatch.setenv(
        "EDITOR_JS_ALLOWED_ATTRIBUTES",
        json.dumps(allowed_attributes),
    )
    cleaner_settings.reload()

    assert_paragraph_cleaned(html_input, expected_output)


@pytest.mark.parametrize(
    ("_case", "html_input", "expected_output"),
    [
        (
            "Does not drop allowed tag values",
            '<a href="https://example.com" is="allowed">Link</a>',
            '<a href="https://example.com" is="allowed">Link</a>',
        ),
        (
            "Removes attribute value if not allowed",
            '<a href="https://example.com" is="bad">Link</a>',
            '<a href="https://example.com">Link</a>',
        ),
        (
            "Keeps the attribute values if ALL words match",
            '<a href="https://example.com" is="multiple words">Link</a>',
            '<a href="https://example.com" is="multiple words">Link</a>',
        ),
        (
            "Drops the attribute if the values isn't exactly equal",
            '<a href="https://example.com" is="this is allowed here">Link</a>',
            # ammonia doesn't attempt to parse the list of attributes (which is good)
            '<a href="https://example.com">Link</a>',
        ),
        (
            # rel is a special case, there is special logic in ammonia thus we need
            # to make sure it doesn't drop these
            "a[rel] values are kept when it matches",
            '<a href="https://example.com" rel="noopener noreferrer">Link</a>',
            '<a href="https://example.com" rel="noopener noreferrer">Link</a>',
        ),
        (
            "a[rel] is dropped when it does not match",
            '<a href="https://example.com" rel="bad">Link</a>',
            '<a href="https://example.com">Link</a>',
        ),
        (
            "If <a> is allowed, shouldn't be able to use it for <div>",
            '<div is="allowed">x</div>',
            "<div>x</div>",
        ),
    ],
)
def test_clean_text_data_block_allow_custom_attribute_values(
    monkeypatch,
    cleaner_settings,
    _case: str,
    html_input: str,
    expected_output: str,
):
    monkeypatch.setenv(
        "EDITOR_JS_ALLOWED_ATTRIBUTE_VALUES",
        json.dumps(
            {
                "a": {
                    "is": ["allowed", "multiple words"],
                    "rel": ["noopener noreferrer"],
                }
            }
        ),
    )
    cleaner_settings.reload()

    assert_paragraph_cleaned(html_input, expected_output)


@pytest.mark.parametrize(
    ("input_html", "expected_output_html"),
    [
        (
            (
                "The Saleor Winter Sale is snowed under with seasonal offers. Unreal products "
                "at unreal prices. Literally, they are not real products, but the Saleor demo "
                "store is a genuine e-commerce leader."
                'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/"></a>'
                'The Saleor Sale is snowed <a href="https://docs.saleor.io/">Test</a>.'
                ""
                "The Saleor Winter Sale is snowed <a >"
            ),
            (
                "The Saleor Winter Sale is snowed under with seasonal offers. Unreal products "
                "at unreal prices. Literally, they are not real products, but the Saleor demo "
                "store is a genuine e-commerce leader."
                'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/"></a>'
                'The Saleor Sale is snowed <a href="https://docs.saleor.io/">Test</a>.'
                ""
                "The Saleor Winter Sale is snowed <a></a>"
            ),
        )
    ],
)
def test_clean_editor_js(input_html: str, expected_output_html: str, no_link_rel):
    # given
    input_data = {"blocks": [{"data": {"text": input_html}, "type": "paragraph"}]}
    expected_output = {
        "blocks": [{"data": {"text": expected_output_html}, "type": "paragraph"}]
    }

    # when
    result = clean_editorjs(input_data, for_django=False)

    # then
    assert result == expected_output

    # when
    result = editorjs_to_text(input_data)

    # then
    assert result == strip_tags(expected_output_html)


@pytest.mark.parametrize(
    ("_case", "input_data", "expected_dict_out"),
    [
        ("No block provided", {}, {}),
        ("Empty block list", {"blocks": []}, {"blocks": []}),
    ],
)
def test_clean_editor_js_no_blocks(
    _case: str, input_data: dict, expected_dict_out: dict
):
    result = clean_editorjs(input_data, for_django=False)
    assert result == expected_dict_out

    result = editorjs_to_text(input_data)
    assert result == ""


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


def test_clean_editor_js_for_list(no_link_rel):
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "The Saleor Winter Sale is snowed "
                    '<a href="https://docs.saleor.io/">Test</a>.'
                },
                "type": "paragraph",
            },
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "It is a block-styled editor "
                        '<a href="https://docs.saleor.io/"></a>.',
                        "It returns clean data output in JSON",
                        "Designed to be extendable and pluggable with a simple API",
                        "",
                    ],
                },
            },
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    assert result == data

    # when
    result = editorjs_to_text(data)

    # then
    assert result == strip_tags(
        "The Saleor Winter Sale is snowed "
        '<a href="https://docs.saleor.io/">Test</a>.'
        " It is a block-styled editor "
        '<a href="https://docs.saleor.io/">.'
        " It returns clean data output in JSON"
        " Designed to be extendable and pluggable with a simple API"
    )


def test_clean_editor_js_for_list_invalid_url():
    # given
    url_invalid = "javascript:alert(1)"
    url_valid = "https://github.com/editor-js"
    text1 = 'The Saleor Winter Sale is snowed <a href="{}">. Test.'
    item_text_with_url = 'It is a block-styled editor <a href="{}">.'

    data = {
        "blocks": [
            {"data": {"text": text1.format(url_invalid)}, "type": "paragraph"},
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "It returns clean data output in JSON",
                        item_text_with_url.format(url_valid),
                        "Designed to be extendable and pluggable with a simple API",
                    ],
                },
            },
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    # Paragraph with invalid url should be cleaned
    assert "javascript:" not in result["blocks"][0]["data"]["text"]

    # List item with valid url should be preserved
    assert url_valid in result["blocks"][1]["data"]["items"][1]

    # Unchanged
    assert (
        result["blocks"][1]["data"]["items"][0] == data["blocks"][1]["data"]["items"][0]
    )
    assert (
        result["blocks"][1]["data"]["items"][2] == data["blocks"][1]["data"]["items"][2]
    )


def test_clean_editor_js_for_complex_description(no_link_rel):
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "The Saleor Winter Sale is snowed "
                    '<a href="https://docs.saleor.io/">Test</a>.'
                },
                "type": "paragraph",
            },
            {
                "data": {
                    "text": "The one thing you be sure of is: Polish winters are quite"
                    " unpredictable. The coldest months are January and February"
                    " with temperatures around -3.0 °C (on average), but the"
                    " weather might change from mild days with over 5 °C and"
                    " days where temperatures may drop to −20 °C (−4 °F)."
                },
                "type": "paragraph",
            },
            {
                "type": "list",
                "data": {
                    "style": "ordered",
                    "items": [
                        "Bring your coat",
                        "warm clothes",
                    ],
                },
            },
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "test item",
                        "item test",
                    ],
                },
            },
            {
                "type": "image",
                "data": {
                    "file": {
                        "url": "https://codex.so/public/app/img/external/codex2x.png"
                    },
                    "caption": "Test caption",
                    "withBorder": False,
                    "stretched": False,
                    "withBackground": False,
                },
            },
            {
                "type": "embed",
                "data": {
                    "service": "youtube",
                    "source": "https://www.youtube.com/erz",
                    "embed": "https://www.youtube.com/embed/erz",
                    "width": 580,
                    "height": 320,
                    "caption": "How To Use",
                },
            },
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    assert result == data

    # when
    result = editorjs_to_text(data)

    # then
    assert result == strip_tags(
        "The Saleor Winter Sale is snowed "
        '<a href="https://docs.saleor.io/">Test</a>.'
        " The one thing you be sure of is: Polish winters are quite"
        " unpredictable. The coldest months are January and February"
        " with temperatures around -3.0 °C (on average), but the"
        " weather might change from mild days with over 5 °C and"
        " days where temperatures may drop to −20 °C (−4 °F)."
        " Bring your coat"
        " warm clothes"
        " test item"
        " item test"
        " https://codex.so/public/app/img/external/codex2x.png"
        " Test caption"
        " https://www.youtube.com/erz"
        " https://www.youtube.com/embed/erz"
        " How To Use"
    )


def test_clean_editor_js_for_malicious_value():
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "<img src=x onerror=alert(1)><script>alert(2);</script>Check"
                },
                "type": "paragraph",
            }
        ]
    }

    # when
    result = clean_editorjs(data, for_django=False)

    # then
    # Malicious elements should be stripped.
    # nh3 allows img but strips onerror. script is removed.
    text = result["blocks"][0]["data"]["text"]
    assert "onerror" not in text
    assert "<script>" not in text
    assert "alert" not in text
    assert "Check" in text


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


def test_clean_editorjs_image_can_put_extras():
    """Ensure user can provide extra fields in 'data.image.file' without error.

    This shouldn't be rejected, but any extra field provided should be automatically
    deleted by Pydantic in order to prevent XSS attacks against unknown/unsupported
    fields.

    This is needed due to EditorJS specs stating that data.image.file can contain
    anything.
    """

    input_data = {
        "blocks": [
            {
                "type": "image",
                "data": {
                    "file": {
                        # OK: known field
                        "url": "https://example.com/image.png",
                        # Unknown fields, thus should be dropped (but shouldn't return an
                        # error)
                        "foo": "bar",
                        DIRTY: DIRTY,
                    }
                },
            }
        ]
    }
    expected_output = {
        "blocks": [
            {
                "type": "image",
                "data": {"file": {"url": "https://example.com/image.png"}},
            }
        ]
    }

    actual_output = clean_editorjs(input_data, for_django=False)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    ("_case", "data", "expected_results", "expected_errors"),
    [
        (
            "Should clean list items",
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": ["<img src=invalid onerror=alert(1) />"],
                },
            },
            # Expects:
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": ['<img src="invalid">'],
                },
            },
            None,
        ),
        (
            "Should be able to clean when 1st item is empty",
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": ["", "<img src=invalid onerror=alert(1) />"],
                },
            },
            # Expects:
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": ["", '<img src="invalid">'],
                },
            },
            None,
        ),
        (
            "Should clean the style field",
            {
                "type": "list",
                "data": {
                    "style": 'unordered"/><script>alert(1) <!--',
                    "items": [],
                },
            },
            # Expects:
            None,
            [
                {
                    "loc": ("blocks", 0, "list", "data", "style"),
                    "msg": "Input should be 'ordered', 'unordered' or 'checklist'",
                }
            ],
        ),
    ],
)
def test_clean_editorjs_legacy(
    _case: str,
    data: dict,
    expected_results: dict | None,
    expected_errors: list[dict] | None,
):
    """Ensure that legacy lists (non-nested) are supported.

    Format: https://github.com/editor-js/list-legacy/blob/381254443234ebbec9cc508fa8a7b982b6a79418/README.md#output-data
    """

    data = {"blocks": [data]}

    actual_results = None
    err = None

    try:
        actual_results = clean_editorjs(data, for_django=False)
    except pydantic_core.ValidationError as exc:
        err = exc

    if expected_errors is not None:
        assert err is not None
        assert_pydantic_errors(err, expected_errors)
    else:
        assert err is None
        blocks = actual_results["blocks"]
        assert len(blocks) == 1
        assert blocks == [expected_results]


@pytest.mark.parametrize(
    ("_case", "data"),
    [
        (
            "No Items",
            {
                "type": "list",
                "data": {
                    "items": [],  # empty list should work fine
                },
            },
        ),
        (
            "Empty item",
            {
                "type": "list",
                "data": {
                    "items": [""],  # empty item should work fine
                },
            },
        ),
        (
            "Basic HTML",
            {
                "type": "list",
                "data": {
                    # Basic HTML shouldn't cause differences or any issues
                    "items": ["<strong>Apple</strong>", "Kiwi"],
                },
            },
        ),
        (
            "Meta fields with allowed types",
            {
                "type": "list",
                "data": {
                    "meta": {
                        "integer": 1,
                        "boolean": True,
                        "float": 3.14,
                        "string": "my string",
                        "null": None,
                    },
                },
            },
        ),
        (
            "Null meta is OK",
            {
                "type": "list",
                "data": {
                    "meta": None,
                },
            },
        ),
    ],
)
def test_clean_editorjs_legacy_works_for_valid_inputs(_case: str, data: dict):
    data = {"blocks": [data]}

    expected = deepcopy(data)
    actual = clean_editorjs(data, for_django=False)

    # Valid data shouldn't have alterated
    assert actual == expected


@pytest.mark.parametrize(
    ("_case", "data", "expected_error"),
    [
        ("Missing type", {}, "Unable to extract tag using discriminator 'type'"),
        (
            "Items invalid type",
            {
                "type": "list",
                "data": {
                    "items": 1,
                },
            },
            "Input should be a valid list",
        ),
        (
            "Items invalid type inside array",
            {
                "type": "list",
                "data": {
                    "items": [1],
                },
            },
            "Input should be a valid dictionary or instance of EditorJSNestedListItemModel",
        ),
        (
            "Items invalid type inside array after valid value",
            {
                "type": "list",
                "data": {
                    "items": ["valid", 1],
                },
            },
            "Input should be a valid dictionary or instance of EditorJSNestedListItemModel",
        ),
        (
            "Items invalid type inside style field",
            {
                "type": "list",
                "data": {
                    "style": 1,
                    "items": ["valid"],
                },
            },
            "Input should be 'ordered', 'unordered' or 'checklist'",
        ),
    ],
)
def test_clean_editorjs_legacy_rejects_invalid(
    _case: str, data: dict, expected_error: str
):
    """Ensure when invalid data is provided as legacy lists, it's rejected."""

    data = {"blocks": [data]}

    with pytest.raises(pydantic_core.ValidationError) as exc:
        clean_editorjs(data, for_django=False)

    assert expected_error in str(exc.value)


@pytest.mark.parametrize(
    ("_case", "data", "expected_results"),
    [
        (
            "Deep lists should be cleaned properly",
            # DATA
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "meta": {
                        # NOTE: key is considered as "trusted" but value isn't
                        "key": DIRTY,
                    },
                    "items": [
                        {
                            "content": f"{DIRTY} - depth level 1",
                            "meta": {
                                "key": DIRTY,
                            },
                            "items": [
                                {
                                    "content": f"{DIRTY} - depth level 2",
                                    "meta": {
                                        "key": DIRTY,
                                    },
                                    "items": [
                                        {
                                            "content": f"{DIRTY} - depth level 3",
                                            "meta": {
                                                "key": DIRTY,
                                            },
                                            "items": [
                                                {
                                                    "content": f"{DIRTY} - depth level 4",
                                                    "meta": {},
                                                    "items": [],
                                                }
                                            ],
                                        },
                                        {
                                            "content": f"{DIRTY} - depth level 3",
                                            "meta": {
                                                "key": DIRTY,
                                            },
                                            "items": [],
                                        },
                                    ],
                                },
                                {
                                    "content": f"{DIRTY} - depth level 2",
                                    "meta": {
                                        "key": DIRTY,
                                    },
                                    "items": [],
                                },
                            ],
                        },
                        {
                            "content": f"{DIRTY} - depth level 1",
                            "meta": {
                                "key": DIRTY,
                            },
                            "items": [],
                        },
                        {
                            "content": f"{DIRTY} - Item next to the previous level 1 item",
                            "meta": {
                                "key": DIRTY,
                            },
                            "items": [
                                {
                                    "content": f"Another level inside level 1 (again) {DIRTY}",
                                    "meta": {
                                        "key": DIRTY,
                                    },
                                    "items": [],
                                }
                            ],
                        },
                    ],
                },
            },
            # RESULTS
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "meta": {
                        "key": CLEAN,
                    },
                    "items": [
                        {
                            "content": f"{CLEAN} - depth level 1",
                            "meta": {
                                "key": CLEAN,
                            },
                            "items": [
                                {
                                    "content": f"{CLEAN} - depth level 2",
                                    "meta": {
                                        "key": CLEAN,
                                    },
                                    "items": [
                                        {
                                            "content": f"{CLEAN} - depth level 3",
                                            "meta": {
                                                "key": CLEAN,
                                            },
                                            "items": [
                                                {
                                                    "content": f"{CLEAN} - depth level 4",
                                                    "meta": {},
                                                    "items": [],
                                                }
                                            ],
                                        },
                                        {
                                            "content": f"{CLEAN} - depth level 3",
                                            "meta": {
                                                "key": CLEAN,
                                            },
                                            "items": [],
                                        },
                                    ],
                                },
                                {
                                    "content": f"{CLEAN} - depth level 2",
                                    "meta": {
                                        "key": CLEAN,
                                    },
                                    "items": [],
                                },
                            ],
                        },
                        {
                            "content": f"{CLEAN} - depth level 1",
                            "meta": {
                                "key": CLEAN,
                            },
                            "items": [],
                        },
                        {
                            "content": f"{CLEAN} - Item next to the previous level 1 item",
                            "meta": {
                                "key": CLEAN,
                            },
                            "items": [
                                {
                                    "content": f"Another level inside level 1 (again) {CLEAN}",
                                    "meta": {
                                        "key": CLEAN,
                                    },
                                    "items": [],
                                }
                            ],
                        },
                    ],
                },
            },
        ),
    ],
)
def test_cleans_editorjs_nested_lists(_case: str, data: dict, expected_results: dict):
    data = {"blocks": [data]}

    actual = clean_editorjs(data, for_django=False)

    blocks = actual["blocks"]
    assert len(blocks) == 1

    assert blocks[0] == expected_results


@pytest.mark.parametrize(
    ("_case", "data", "expected_errors"),
    [
        (
            "Item contains invalid type",
            {
                "type": "list",
                "data": {
                    "items": [
                        {
                            "content": "Apples",
                            "items": [
                                # OK: valid
                                {
                                    "content": "Red",
                                    "meta": {},
                                    "items": [],
                                },
                                # Not OK: invalid
                                1,
                            ],
                        },
                    ],
                },
            },
            [
                {
                    "loc": (
                        "blocks",
                        0,
                        "list",
                        "data",
                        "items",
                        0,
                        "EditorJSNestedListItemModel",
                        "items",
                        1,
                    ),
                    "msg": "Input should be a valid dictionary or instance of EditorJSNestedListItemModel",
                },
                {
                    "loc": (
                        "blocks",
                        0,
                        "list",
                        "data",
                        "items",
                        0,
                        "function-after[_clean_text(), str]",
                    ),
                    "msg": "Input should be a valid string",
                },
            ],
        ),
        (
            "Invalid type in meta",
            {
                "type": "list",
                "data": {"meta": {"key": object()}},
            },
            [
                {
                    "loc": ("blocks", 0, "list", "data", "meta", "key", "int"),
                    "msg": "Input should be a valid integer",
                },
                {
                    "loc": ("blocks", 0, "list", "data", "meta", "key", "float"),
                    "msg": "Input should be a valid number",
                },
                {
                    "loc": ("blocks", 0, "list", "data", "meta", "key", "bool"),
                    "msg": "Input should be a valid boolean",
                },
                {
                    "loc": (
                        "blocks",
                        0,
                        "list",
                        "data",
                        "meta",
                        "key",
                        "function-after[_clean_text(), str]",
                    ),
                    "msg": "Input should be a valid string",
                },
            ],
        ),
        (
            "Too many fields in meta",
            {
                "type": "list",
                "data": {"meta": {str(i): i for i in range(11)}},
            },
            [
                {
                    "loc": ("blocks", 0, "list", "data", "meta"),
                    "msg": "Value error, Invalid meta block for EditorJS: too many fields",
                }
            ],
        ),
        (
            "Keys must be a string",
            {"type": "list", "data": {"meta": {1: "string"}}},
            [
                {
                    "loc": ("blocks", 0, "list", "data", "meta", 1, "[key]"),
                    "msg": "Input should be a valid string",
                }
            ],
        ),
    ],
)
def test_clean_editorjs_rejects_invalid_nested_lists(
    _case: str,
    data: dict,
    expected_errors: list[dict],
    settings,
):
    """Ensure when invalid data is provided a nested lists, it's rejected."""

    settings.EDITOR_JS_LISTS_MAX_DEPTH = 3

    data = {"blocks": [data]}

    with pytest.raises(pydantic_core.ValidationError) as exc:
        clean_editorjs(data, for_django=False)

    assert_pydantic_errors(exc.value, expected_errors)


def test_clean_editorjs_rejects_too_deep_nested_list(settings):
    """A nested list that's too deep should be rejected as it's likely malicious."""

    settings.EDITOR_JS_LISTS_MAX_DEPTH = 3

    data = {
        "blocks": [
            {
                "type": "list",
                "data": {
                    "items": [
                        {
                            "items": [
                                {
                                    "items": [
                                        {
                                            "items": [
                                                {"items": [{"items": [{"items": []}]}]}
                                            ]
                                        }
                                    ]
                                },
                            ],
                        },
                    ]
                },
            },
        ]
    }

    with pytest.raises(
        django.core.exceptions.ValidationError,
        match="Invalid EditorJS list: maximum nesting level exceeded",
    ):
        clean_editorjs(data, for_django=False)


def test_heading_level_cleaned():
    """Ensure heading blocks have their heading level cleaned."""

    data_input = {"type": "header", "data": {"level": DIRTY}}

    with pytest.raises(pydantic_core.ValidationError) as exc:
        clean_editorjs({"blocks": [data_input]}, for_django=False)

    error_list = exc.value.errors()
    assert len(error_list) == 1

    [err] = error_list
    assert err["input"] == DIRTY
    assert err["loc"] == ("blocks", 0, "header", "data", "level")
    assert err["msg"] == "Value error, Value must be an integer"


@pytest.mark.parametrize("block_type", ["image", "quote", "embed"])
@pytest.mark.parametrize(
    ("data_field", "expected_results", "expected_errors"),
    [
        (
            {"width": "1", "height": "1"},
            # Should normalize to integer
            {"width": 1, "height": 1},
            None,
        ),
        (
            # Should be kept as is
            {"width": 1, "height": 1},
            {"width": 1, "height": 1},
            None,
        ),
        (
            {"width": DIRTY},
            None,
            [
                {
                    "msg": "Value error, Value must be an integer",
                    "input": DIRTY,
                }
            ],
        ),
        (
            {"height": DIRTY},
            None,
            [
                {
                    "msg": "Value error, Value must be an integer",
                    "input": DIRTY,
                }
            ],
        ),
    ],
)
def test_cleans_size_caption_blocks(
    block_type: str,
    data_field: dict,
    expected_results: dict | None,
    expected_errors: list[dict] | None,
):
    """Ensure all block types that have a caption field have their size fields cleaned."""

    data = {"blocks": [{"type": block_type, "data": data_field}]}
    error = None
    actual = None

    try:
        actual = clean_editorjs(data, for_django=False)
    except pydantic_core.ValidationError as exc:
        error = exc

    if expected_errors is not None:
        assert error is not None, "Expected an error but didn't find one"
        assert_pydantic_errors(error, expected_errors)
    else:
        assert error is None, "Didn't expect an error"

    if expected_results is not None:
        blocks = actual["blocks"]
        assert len(blocks) == 1
        block = blocks[0]

        assert block["type"] == block_type
        assert block["data"] == expected_results


# Supported: paragraph, header, list (tested in other test cases due to being a complex
# structure), quote, embed, image
@pytest.mark.parametrize(
    ("_case", "data", "expected_data"),
    [
        (
            "Paragraph",
            {
                "type": "paragraph",
                "data": {"text": DIRTY, "alignment": DIRTY, "align": DIRTY},
            },
            {
                "type": "paragraph",
                "data": {"text": CLEAN, "alignment": CLEAN, "align": CLEAN},
            },
        ),
        (
            "Header",
            {"type": "header", "data": {"text": DIRTY, "level": 2}},
            {"type": "header", "data": {"text": CLEAN, "level": 2}},
        ),
        (
            "Quote",
            {
                "type": "quote",
                "data": {
                    "text": DIRTY,
                    "caption": DIRTY,
                    "alignment": DIRTY,
                    "align": DIRTY,
                },
            },
            {
                "type": "quote",
                "data": {
                    "text": CLEAN,
                    "caption": CLEAN,
                    "alignment": CLEAN,
                    "align": CLEAN,
                },
            },
        ),
        (
            "Embed",
            {
                "type": "embed",
                "data": {
                    "service": DIRTY,
                    "source": DIRTY,
                    "embed": DIRTY,
                    "width": 580,
                    "height": 320,
                    "caption": DIRTY,
                },
            },
            {
                "type": "embed",
                "data": {
                    "service": CLEAN,
                    "source": "#invalid",
                    "embed": "#invalid",
                    "width": 580,
                    "height": 320,
                    "caption": CLEAN,
                },
            },
        ),
        (
            "Image",
            {
                "type": "image",
                "data": {
                    "file": {
                        "url": DIRTY,
                    },
                    "url": DIRTY,
                    "caption": DIRTY,
                    "withBorder": False,
                    "withBackground": False,
                    "stretched": True,
                },
            },
            {
                "type": "image",
                "data": {
                    "file": {
                        "url": "#invalid",
                    },
                    "url": "#invalid",
                    "caption": CLEAN,
                    "withBorder": False,
                    "withBackground": False,
                    "stretched": True,
                },
            },
        ),
    ],
)
def test_cleans_all_editor_js_blocks(_case, data, expected_data):
    """Check all block types supported by Saleor and ensure they all gets cleaned."""

    with warnings.catch_warnings(record=True):
        actual = clean_editorjs({"blocks": [data]}, for_django=False)

    assert len(actual["blocks"]) == 1
    actual = actual["blocks"][0]

    assert actual == expected_data


@pytest.mark.parametrize(
    ("for_django", "expected_exception_cls"),
    [
        (True, django.core.exceptions.ValidationError),
        (False, pydantic_core.ValidationError),
    ],
)
def test_converts_exceptions_to_django(
    for_django: bool, expected_exception_cls: type[BaseException]
):
    """Passing ``for_django=True`` it raise a Django exception instead of pydantic."""

    input_data = {"blocks": 1}
    with pytest.raises(expected_exception_cls):
        clean_editorjs(input_data, for_django=for_django)
