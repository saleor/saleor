import pydantic_core
import pytest

from .. import clean_editorjs


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
        clean_editorjs(data)

    assert expected_error in str(exc.value)
