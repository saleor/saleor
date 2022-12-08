import warnings
from unittest import mock

import pytest
from django.utils.html import strip_tags

from ..utils.editorjs import clean_editor_js


@pytest.mark.parametrize(
    "text",
    [
        "The Saleor Winter Sale is snowed under with seasonal offers. Unreal products "
        "at unreal prices. Literally, they are not real products, but the Saleor demo "
        "store is a genuine e-commerce leader.",
        'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/docs/">',
        'The Saleor Sale is snowed <a href="https://docs.saleor.io/docs/">. Test.',
        'The Saleor Winter Sale is snowed <a href="https://docs.saleor.io/docs/">. '
        'Test <a href="https://docs.saleor.io/docs/">.',
        "",
        "The Saleor Winter Sale is snowed <a >",
    ],
)
def test_clean_editor_js(text):
    # given
    data = {"blocks": [{"data": {"text": text}, "type": "paragraph"}]}

    # when
    result = clean_editor_js(data)

    # then
    assert result == data

    # when
    result = clean_editor_js(data, to_string=True)

    # then
    assert result == strip_tags(text)


def test_clean_editor_js_no_blocks():
    # given
    data = {}

    # when
    result = clean_editor_js(data)

    # then
    assert result == data

    # when
    result = clean_editor_js(data, to_string=True)

    # then
    assert result == ""


def test_clean_editor_js_no_data():
    # given
    data = {"blocks": []}

    # when
    result = clean_editor_js(data)

    # then
    assert result == data

    # when
    result = clean_editor_js(data, to_string=True)

    # then
    assert result == ""


@mock.patch("saleor.core.utils.editorjs.parse_url")
def test_clean_editor_js_invalid_url(parse_url_mock):
    # given
    response_mock = mock.Mock()
    response_mock.scheme = "javascript"
    mocked_parse = mock.Mock(return_value=response_mock)
    parse_url_mock.side_effect = mocked_parse

    url = "https://github.com/editor-js"
    text = (
        'The Saleor Winter Sale is snowed under with seasonal offers. <a href="{}"> '
        "Unreal products at unreal prices. Literally, they are not real products, "
        "but the Saleor demo store is a genuine e-commerce leader."
    )

    data = {"blocks": [{"data": {"text": text.format(url)}, "type": "paragraph"}]}

    # when
    with warnings.catch_warnings(record=True) as warns:
        result = clean_editor_js(data)

        assert len(warns) == 1
        assert f"An invalid url was sent: {url}" in str(warns[0].message)

    # then
    new_url = "#invalid"
    assert result["blocks"][0]["data"]["text"] == text.format(new_url)


def test_clean_editor_js_for_list():
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "The Saleor Winter Sale is snowed "
                    '<a href="https://docs.saleor.io/docs/">. Test.'
                },
                "type": "paragraph",
            },
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "It is a block-styled editor "
                        '<a href="https://docs.saleor.io/docs/">.',
                        "It returns clean data output in JSON",
                        "Designed to be extendable and pluggable with a simple API",
                        "",
                    ],
                },
            },
        ]
    }

    # when
    result = clean_editor_js(data)

    # then
    assert result == data

    # when
    result = clean_editor_js(data, to_string=True)

    # then
    assert result == strip_tags(
        "The Saleor Winter Sale is snowed "
        '<a href="https://docs.saleor.io/docs/">. Test.'
        " It is a block-styled editor "
        '<a href="https://docs.saleor.io/docs/">.'
        " It returns clean data output in JSON"
        " Designed to be extendable and pluggable with a simple API"
    )


@mock.patch("saleor.core.utils.editorjs.parse_url")
def test_clean_editor_js_for_list_invalid_url(parse_url_mock):
    # given
    response_mock = mock.Mock()
    response_mock.scheme = "javascript"
    mocked_parse = mock.Mock(return_value=response_mock)
    parse_url_mock.side_effect = mocked_parse

    url1 = "https://docs.saleor.io/docs/"
    url2 = "https://github.com/editor-js"
    text1 = 'The Saleor Winter Sale is snowed <a href="{}">. Test.'
    item_text_with_url = 'It is a block-styled editor <a href="{}">.'

    data = {
        "blocks": [
            {"data": {"text": text1.format(url1)}, "type": "paragraph"},
            {
                "type": "list",
                "data": {
                    "style": "unordered",
                    "items": [
                        "It returns clean data output in JSON",
                        item_text_with_url.format(url2),
                        "Designed to be extendable and pluggable with a simple API",
                    ],
                },
            },
        ]
    }

    # when
    with warnings.catch_warnings(record=True) as warns:
        result = clean_editor_js(data)

        assert len(warns) == 2
        assert f"An invalid url was sent: {url1}" in str(warns[0].message)
        assert f"An invalid url was sent: {url2}" in str(warns[1].message)

    # then
    assert result["blocks"][0]["data"]["text"] == text1.format("#invalid")
    assert result["blocks"][1]["data"]["items"][1] == item_text_with_url.format(
        "#invalid"
    )
    assert (
        result["blocks"][1]["data"]["items"][0] == data["blocks"][1]["data"]["items"][0]
    )
    assert (
        result["blocks"][1]["data"]["items"][2] == data["blocks"][1]["data"]["items"][2]
    )


def test_clean_editor_js_for_complex_description():
    # given
    data = {
        "blocks": [
            {
                "data": {
                    "text": "The Saleor Winter Sale is snowed"
                    '<a href="https://docs.saleor.io/docs/">. Test.'
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
    result = clean_editor_js(data)

    # then
    assert result == data

    # when
    result = clean_editor_js(data, to_string=True)

    # then
    assert result == strip_tags(
        "The Saleor Winter Sale is snowed"
        '<a href="https://docs.saleor.io/docs/">. Test.'
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
