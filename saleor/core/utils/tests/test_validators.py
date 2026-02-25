import pytest

from ..validators import get_mime_type, is_image_mimetype, is_valid_image_content_type


def test_is_image_mimetype_valid_mimetype():
    # given
    valid_mimetype = "image/jpeg"

    # when
    result = is_image_mimetype(valid_mimetype)

    # then
    assert result


def test_is_image_mimetype_invalid_mimetype():
    # given
    invalid_mimetype = "application/javascript"

    # when
    result = is_image_mimetype(invalid_mimetype)

    # then
    assert not result


@pytest.mark.parametrize(
    ("content_type", "is_valid"),
    [
        ("image/jpeg", True),
        ("image/jpg", True),
        ("image/png", True),
        ("image/gif", True),
        ("image/bmp", True),
        ("image/tiff", True),
        ("image/webp", True),
        ("image/avif", True),
        ("application/json", False),
        ("text/plain", False),
        ("application/pdf", False),
        (None, False),
    ],
)
def test_is_valid_image_content_type(content_type, is_valid):
    # when
    result = is_valid_image_content_type(content_type)

    # then
    assert result == is_valid


@pytest.mark.parametrize(
    ("content_type_header", "expected_mime_type"),
    [
        (None, None),
        ("", ""),
        ("text/html; charset=utf-8", "text/html"),
        ("text/css; charset=UTF-8", "text/css"),
        ("image/jpeg", "image/jpeg"),
        ("  image/png; charset=binary", "image/png"),
        (" Text/HTML ; Charset=UTF-8 ", "text/html"),
        ("APPLICATION/JSON;CHARSET=UTF-8", "application/json"),
    ],
)
def test_get_mime_type(content_type_header, expected_mime_type):
    assert get_mime_type(content_type_header) == expected_mime_type
