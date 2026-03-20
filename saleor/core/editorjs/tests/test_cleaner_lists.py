from copy import deepcopy

import django.core.exceptions
import pydantic_core
import pytest
from django.utils.html import strip_tags

from .. import clean_editorjs, editorjs_to_text
from .conftest import CLEAN, DIRTY, assert_pydantic_errors

INVALID = object()


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
    result = clean_editorjs(data)

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
    result = clean_editorjs(data)

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
        actual_results = clean_editorjs(data)
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
    actual = clean_editorjs(data)

    # Valid data shouldn't have alterated
    assert actual == expected


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

    actual = clean_editorjs(data)

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
        clean_editorjs(data)

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
        clean_editorjs(data)
