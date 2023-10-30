import pytest
from django.core.exceptions import ValidationError

from ... import __version__
from ...app.validators import AppURLValidator
from ..error_codes import AppErrorCode
from ..manifest_validations import (
    clean_author,
    clean_required_saleor_version,
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
    ("required_version", "version", "satisfied"),
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


@pytest.mark.parametrize(
    ("author", "cleaned"), [(None, None), (" Acme Ltd ", "Acme Ltd")]
)
def test_clean_author(author, cleaned):
    assert clean_author(author) == cleaned


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
def test_brand_validator_with_invalid_logo_url(url):
    with pytest.raises(ValidationError) as error:
        brand_validator({"logo": {"default": url}})
    assert error.value.code == AppErrorCode.INVALID_URL_FORMAT.value
