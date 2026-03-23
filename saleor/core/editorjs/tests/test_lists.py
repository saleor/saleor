import pytest

from ...editorjs import editorjs_to_text


@pytest.mark.parametrize(
    ("_case", "input_data", "expected_output"),
    [
        ("Missing items", {}, ""),
        ("Missing null items", {"items": None}, ""),
        ("Empty list", {"items": []}, ""),
        ("List with 1 item", {"items": ["Item 1"]}, "Item 1"),
        ("List with 2 items", {"items": ["Item 1", "Item 2"]}, "Item 1 Item 2"),
    ],
)
def test_legacy_lists_to_text(_case: str, input_data: dict, expected_output: str):
    """Legacy list format should successfully be transformed to text."""

    data = {"blocks": [{"type": "list", "data": input_data}]}

    actual_output = editorjs_to_text(data)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    ("_case", "input_data", "expected_output"),
    [
        (
            "1-deep list",
            {
                "items": [
                    {
                        "content": "Apples",
                        "meta": {},
                        "items": [],
                    }
                ]
            },
            "Apples",
        ),
        (
            "3-deep list",
            {
                "items": [
                    {
                        "content": "1 deep",
                        "meta": {},
                        "items": [
                            {
                                "content": "2 deep",
                                "meta": {},
                                "items": [
                                    {
                                        "content": "3 deep",
                                        "meta": {},
                                        "items": [],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
            "1 deep 2 deep 3 deep",
        ),
        (
            "List with surrounding items",
            {
                "items": [
                    {
                        "content": "level 1 - 1st member",
                        "meta": {},
                        "items": [],
                    },
                    {
                        "content": "level 1 - 2nd member",
                        "items": [{"items": [{"content": "level 2 member"}]}],
                    },
                    {"content": "level 1 - 3rd member"},
                ]
            },
            (
                "level 1 - 1st member "
                "level 1 - 2nd member "
                "level 2 member "
                "level 1 - 3rd member"
            ),
        ),
    ],
)
def test_nested_lists_to_text(_case: str, input_data: dict, expected_output: str):
    """Nested list format should successfully be transformed to text."""

    data = {"blocks": [{"type": "list", "data": input_data}]}

    actual_output = editorjs_to_text(data)
    assert actual_output == expected_output
