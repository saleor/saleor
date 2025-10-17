from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ....product.error_codes import ProductErrorCode
from ..validators.file import (
    clean_image_file,
    is_image_mimetype,
    is_image_url,
    is_supported_image_mimetype,
    is_valid_image_content_type,
)


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


def test_is_supported_image_mimetype_valid_mimetype():
    # given
    valid_mimetype = "image/jpeg"

    # when
    result = is_supported_image_mimetype(valid_mimetype)

    # then
    assert result


def test_is_supported_image_mimetype_invalid_mimetype():
    # given
    invalid_mimetype = "application/javascript"

    # when
    result = is_supported_image_mimetype(invalid_mimetype)

    # then
    assert not result


@pytest.mark.parametrize(
    ("content_type", "is_valid"),
    [
        ("image/jpeg", True),
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


def test_clean_image_file():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    field = "image"

    img = SimpleUploadedFile("product.jpg", img_data.getvalue(), "image/jpeg")

    # when & then
    clean_image_file({field: img}, field, ProductErrorCode)


def test_clean_image_file_invalid_content_type():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    img = SimpleUploadedFile("product.jpg", img_data.getvalue(), "text/plain")
    field = "image"

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert exc.value.args[0][field].message == "Invalid file type."


def test_clean_image_file_no_file():
    # given
    field = "image"

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: None}, field, ProductErrorCode)

    # then
    assert exc.value.args[0][field].message == "File is required."


def test_clean_image_file_no_file_extension():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    img = SimpleUploadedFile("product", img_data.getvalue(), "image/jpeg")
    field = "image"

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert exc.value.args[0][field].message == "Lack of file extension."


def test_clean_image_file_invalid_file_extension():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    img = SimpleUploadedFile("product.txt", img_data.getvalue(), "image/jpeg")
    field = "image"

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert (
        exc.value.args[0][field].message
        == "Invalid file extension. Image file required."
    )


def test_clean_image_file_file_extension_not_supported_by_thumbnails():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    img = SimpleUploadedFile("product.pxr", img_data.getvalue(), "image/jpeg")
    field = "image"

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert (
        exc.value.args[0][field].message
        == "Invalid file extension. Image file required."
    )


def test_clean_image_file_issue_with_file_opening(monkeypatch):
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    field = "image"

    error_msg = "Test syntax error"
    image_file_mock = Mock(side_effect=SyntaxError(error_msg))
    monkeypatch.setattr(
        "saleor.graphql.core.validators.file.Image.open", image_file_mock
    )
    img = SimpleUploadedFile("product.jpg", img_data.getvalue(), "image/jpeg")

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert error_msg in exc.value.args[0][field].message


def test_clean_image_file_exif_validation_raising_error(monkeypatch):
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    field = "image"

    error_msg = "Test syntax error"
    image_file_mock = Mock(side_effect=SyntaxError(error_msg))
    monkeypatch.setattr(
        "saleor.graphql.core.validators.file._validate_image_exif", image_file_mock
    )
    img = SimpleUploadedFile("product.jpg", img_data.getvalue(), "image/jpeg")

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    assert error_msg in exc.value.args[0][field].message


@patch("saleor.thumbnail.utils.magic.from_buffer")
def test_clean_image_file_invalid_image_mime_type(from_buffer_mock):
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="WEBP")
    field = "image"

    invalid_mime_type = "application/x-empty"
    from_buffer_mock.return_value = invalid_mime_type
    img = SimpleUploadedFile("product.webp", img_data.getvalue(), "image/webp")

    # when
    with pytest.raises(ValidationError) as exc:
        clean_image_file({field: img}, field, ProductErrorCode)

    # then
    error_msg = f"Unsupported image MIME type: {invalid_mime_type}"
    assert error_msg in exc.value.args[0][field].message


def test_clean_image_file_with_captialized_extension():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    field = "image"

    img = SimpleUploadedFile("product.JPG", img_data.getvalue(), "image/jpeg")

    # when & then
    clean_image_file({field: img}, field, ProductErrorCode)


def test_clean_image_file_in_avif_format():
    # given
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="AVIF")
    field = "image"

    img = SimpleUploadedFile("product.jpg", img_data.getvalue(), "image/avif")

    # when & then
    clean_image_file({field: img}, field, ProductErrorCode)


@pytest.mark.parametrize(
    ("url", "is_valid"),
    [
        ("http://example.com/valid_image.jpg", True),
        ("https://example.com/valid_image.png", True),
        ("http://example.com/valid_image.jpeg", True),
        ("http://example.com/valid_image.gif", True),
        ("http://example.com/valid_image.bmp", True),
        ("http://example.com/valid_image.tiff", True),
        ("http://example.com/valid_image.webp", True),
        ("https://example.com/valid_image.webp", True),
        ("http://example.com/valid_image.avif", True),
        ("http://example.com/invalid_image.pdf", False),
        ("http://example.com/invalid_image.docx", False),
        ("http://example.com/invalid_image.exe", False),
        ("http://example.com/invalid_image.txt", False),
    ],
)
def test_is_image_url(url, is_valid):
    # when
    result = is_image_url(url)

    # then
    assert result is is_valid
