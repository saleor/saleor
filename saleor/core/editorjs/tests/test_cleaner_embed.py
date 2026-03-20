import pydantic_core
import pytest

from .. import clean_editorjs
from .conftest import DIRTY, assert_pydantic_errors


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
