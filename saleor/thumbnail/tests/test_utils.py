import pytest

from ..utils import get_thumbnail_size


@pytest.mark.parametrize(
    "size, expected_value",
    [(1, 32), (16, 32), (60, 64), (80, 64), (256, 256), (8000, 4096), (15000, 4096)],
)
def test_get_thumbnail_size(size, expected_value):
    # when
    returned_size = get_thumbnail_size(size)

    # then
    assert returned_size == expected_value
