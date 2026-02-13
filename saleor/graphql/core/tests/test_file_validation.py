from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ....core.error_codes import UploadErrorCode
from ....product.error_codes import ProductErrorCode
from ..validators.file import (
    clean_image_file,
    detect_mime_type,
    get_mime_type,
    is_image_mimetype,
    is_supported_image_mimetype,
    is_valid_image_content_type,
    validate_upload_file,
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


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("test.jpg", "image/jpeg"),
        ("test.jpeg", "image/jpeg"),
        ("test.JPG", "image/jpeg"),  # case insensitive
        ("test.png", "image/png"),
        ("test.gif", "image/gif"),
        ("test.webp", "image/webp"),
        ("file.txt", "text/plain"),
        ("data.csv", "text/csv"),
        ("video.mp4", "video/mp4"),
        ("video.webm", "video/webm"),
        ("audio.mp3", "audio/mpeg"),
        ("audio.m4a", "audio/mp4"),
    ],
)
@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_validate_upload_file_valid_files(from_buffer_mock, filename, mime_type):
    # given
    from_buffer_mock.return_value = mime_type
    file_data = SimpleUploadedFile(filename, b"content", content_type=mime_type)

    # when & then
    validate_upload_file(file_data, UploadErrorCode, "file")


@pytest.mark.parametrize(
    ("filename", "detected_mime_type"),
    [
        # Unsupported mime types
        ("test.html", "text/html"),
        ("test.svg", "image/svg+xml"),
        ("archive.zip", "application/zip"),
        ("archive.rar", "application/x-rar-compressed"),
        ("test.js", "application/javascript"),
        ("test.xml", "application/xml"),
        ("archive.tar.gz", "application/gzip"),
    ],
)
@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_validate_upload_file_unsupported_mime_type(
    from_buffer_mock, filename, detected_mime_type
):
    # given
    from_buffer_mock.return_value = detected_mime_type
    file_data = SimpleUploadedFile(filename, b"content", content_type="image/jpeg")

    # when
    with pytest.raises(ValidationError) as exc:
        validate_upload_file(file_data, UploadErrorCode, "file")

    # then
    assert exc.value.args[0]["file"].code == UploadErrorCode.UNSUPPORTED_MIME_TYPE.value


@pytest.mark.parametrize(
    ("filename", "detected_mime_type"),
    [
        # Extension mismatch - actual content doesn't match extension
        ("test.png", "image/jpeg"),
        ("test.jpg", "image/png"),
        ("test.pdf", "image/jpeg"),
        # Missing extension
        ("test", "image/jpeg"),
        ("data", "text/csv"),
    ],
)
@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_validate_upload_file_invalid_file_type(
    from_buffer_mock, filename, detected_mime_type
):
    # given
    from_buffer_mock.return_value = detected_mime_type
    file_data = SimpleUploadedFile(filename, b"content", content_type="image/jpeg")

    # when
    with pytest.raises(ValidationError) as exc:
        validate_upload_file(file_data, UploadErrorCode, "file")

    # then
    assert exc.value.args[0]["file"].code == UploadErrorCode.INVALID_FILE_TYPE.value


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_validate_upload_file_detects_spoofed_content_type(from_buffer_mock):
    """Test that actual file content is checked, not content_type header.

    This verifies the security fix: an attacker cannot upload malicious HTML
    by setting content_type header to image/jpeg if the actual file is HTML.
    """
    # given - attacker tries to upload HTML with fake image content_type header
    from_buffer_mock.return_value = "text/html"  # actual content is HTML
    file_data = SimpleUploadedFile(
        "malicious.html",
        b"<html><script>alert('XSS')</script></html>",
        content_type="image/jpeg",  # spoofed content type
    )

    # when
    with pytest.raises(ValidationError) as exc:
        validate_upload_file(file_data, UploadErrorCode, "file")

    # then - should be rejected based on actual content, not header
    assert exc.value.args[0]["file"].code == UploadErrorCode.UNSUPPORTED_MIME_TYPE.value


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_detect_mime_type_success(from_buffer_mock):
    # given
    from_buffer_mock.return_value = "image/jpeg"
    file_data = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")

    # when
    mime_type = detect_mime_type(file_data)

    # then
    assert mime_type == "image/jpeg"
    from_buffer_mock.assert_called_once()


@patch("saleor.graphql.core.validators.file.magic.from_buffer")
def test_detect_mime_type_reads_file_content(from_buffer_mock):
    # given
    from_buffer_mock.return_value = "image/png"
    file_data = SimpleUploadedFile(
        "test.jpg", b"PNG_CONTENT", content_type="image/jpeg"
    )

    # when
    mime_type = detect_mime_type(file_data)

    # then
    assert mime_type == "image/png"
    # Verify magic was called with actual file content, not headers
    from_buffer_mock.assert_called_once_with(b"PNG_CONTENT", mime=True)
