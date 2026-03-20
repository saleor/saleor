import json
import warnings

import django.core.exceptions
import pydantic_core
import pytest
from django.utils.html import strip_tags

from .. import clean_editorjs, editorjs_to_text
from .conftest import CLEAN, DIRTY, XSS_URLS


def assert_paragraph_cleaned(text_input: str, expected_text_output: str) -> None:
    input = {"blocks": [{"type": "paragraph", "data": {"text": text_input}}]}
    expected = {
        "blocks": [{"type": "paragraph", "data": {"text": expected_text_output}}]
    }

    actual = clean_editorjs(input, for_django=False)
    assert actual == expected


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
