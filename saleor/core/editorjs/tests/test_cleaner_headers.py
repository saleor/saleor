import pydantic_core
import pytest

from .. import clean_editorjs
from .conftest import DIRTY


def test_heading_level_cleaned():
    """Ensure heading blocks have their heading level cleaned."""

    data_input = {"type": "header", "data": {"level": DIRTY}}

    with pytest.raises(pydantic_core.ValidationError) as exc:
        clean_editorjs({"blocks": [data_input]})

    error_list = exc.value.errors()
    assert len(error_list) == 1

    [err] = error_list
    assert err["input"] == DIRTY
    assert err["loc"] == ("blocks", 0, "header", "data", "level")
    assert err["msg"] == "Value error, Value must be an integer"
