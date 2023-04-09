from unittest import mock

import pytest
import requests
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from ... import __version__
from ...app.validators import AppURLValidator
from ..error_codes import AppErrorCode
from ..manifest_validations import (
    clean_author,
    clean_required_saleor_version,
    fetch_icon_image,
    parse_version,
)
from ..validators import brand_validator


def test_validate_url():
    url_validator = AppURLValidator()
    url = "http://otherapp:3000"
    assert url_validator(url) is None


def test_validate_invalid_url():
    url_validator = AppURLValidator()
    url = "otherapp:3000"
    with pytest.raises(ValidationError):
        url_validator(url)


def test_parse_version():
    assert str(parse_version(__version__)) == __version__


@pytest.mark.parametrize(
    "required_version,version,satisfied",
    [
        ("*", "3.12.1", True),
        ("3.8 - 3.9 || ~3.10.2 || 3.11.* || 3.12.x", "3.12.1", True),
        ("^3.12.0-0 <=3.14", "3.12.0-a", True),
        ("^3.12", "4.0.0", False),
        ("^3.12", "3.12.0-a", False),
        ("^3.12", "3.13.0-a", True),
    ],
)
def test_clean_required_saleor_version(required_version, version, satisfied):
    cleaned = clean_required_saleor_version(required_version, False, version)
    assert cleaned == {"constraint": required_version, "satisfied": satisfied}


def test_clean_required_saleor_version_optional():
    assert clean_required_saleor_version(None, False) is None


@pytest.mark.parametrize(
    "required_version", ["3.8-3.9", "^3w.11", {"wrong", "data type"}, 3, 3.12]
)
def test_clean_required_saleor_version_with_invalid_range(required_version):
    with pytest.raises(ValidationError) as error:
        clean_required_saleor_version(required_version, False, "3.12.1")
    assert error.value.code == AppErrorCode.INVALID.value


def test_clean_required_saleor_version_raise_for_saleor_version():
    with pytest.raises(ValidationError) as error:
        clean_required_saleor_version("^3.13", True, "3.12.1")
    assert error.value.code == AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value


@pytest.mark.parametrize("author,cleaned", [(None, None), (" Acme Ltd ", "Acme Ltd")])
def test_clean_author(author, cleaned):
    assert clean_author(author) == cleaned


@pytest.fixture
def image_response_mock():
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/png"}
    mock_response.content = b"fake image content"
    return mock_response


@mock.patch("saleor.app.manifest_validations.validate_icon_image")
@mock.patch("saleor.app.manifest_validations.requests.get")
def test_fetch_icon_image(
    mock_get_request, mock_validate_icon_image, image_response_mock
):
    # given
    image_file_format = "png"
    image_url = f"https://example.com/logo.{image_file_format}"
    mock_get_request.return_value.__enter__.return_value = image_response_mock

    # when
    image_file = fetch_icon_image(image_url, "brand.logo.default")

    # then
    mock_get_request.assert_called_once_with(image_url, stream=True, timeout=mock.ANY)
    mock_validate_icon_image.assert_called_once_with(image_file, mock.ANY)
    assert isinstance(image_file, ContentFile)
    assert image_file.read() == image_response_mock.content
    assert image_file.name.endswith(image_file_format)


@mock.patch("saleor.app.manifest_validations.requests.get")
def test_fetch_icon_image_invalid_type(mock_get_request, image_response_mock):
    mock_get_request.return_value.__enter__.return_value = image_response_mock
    image_response_mock.headers = {"content-type": "text/html"}

    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png", "brand.logo.default")
    assert error.value.code == AppErrorCode.INVALID.value


@mock.patch("saleor.app.manifest_validations.requests.get")
def test_fetch_icon_image_network_error(mock_get_request):
    mock_get_request.side_effect = requests.RequestException
    with pytest.raises(ValidationError) as error:
        fetch_icon_image("https://example.com/logo.png", "brand.logo.default")
    assert error.value.code == AppErrorCode.MANIFEST_URL_CANT_CONNECT.value


def test_brand_validator_required_fields():
    with pytest.raises(ValidationError) as error:
        brand_validator({"logo": {}})
    assert error.value.code == AppErrorCode.REQUIRED.value


@pytest.mark.parametrize(
    "url",
    [
        "example.com/logo.png",
        "https://exmple.com/logo",
        "https://exmple.com/logo.jpg",
    ],
)
def test_brand_validator_with_invalid_image_url(url):
    with pytest.raises(ValidationError) as error:
        brand_validator({"logo": {"default": url}})
    assert error.value.code == AppErrorCode.INVALID_URL_FORMAT.value
