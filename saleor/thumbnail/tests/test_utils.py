import pytest

from ..utils import get_thumbnail_size, prepare_thumbnail_file_name


@pytest.mark.parametrize(
    "size, expected_value",
    [(1, 32), (16, 32), (60, 64), (80, 64), (256, 256), (8000, 4096), (15000, 4096)],
)
def test_get_thumbnail_size(size, expected_value):
    # when
    returned_size = get_thumbnail_size(size)

    # then
    assert returned_size == expected_value


@pytest.mark.parametrize(
    "file_name, size, expected_name",
    [
        ("test.txt", 20, "test_thumbnail_20.txt"),
        ("test/test.txt", 20, "test/test_thumbnail_20.txt"),
    ],
)
def test_prepare_thumbnail_file_name(file_name, size, expected_name):
    # when
    thumbnail_name = prepare_thumbnail_file_name(file_name, size)

    # then
    assert thumbnail_name == expected_name
