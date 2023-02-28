import pytest
from django.core.exceptions import ValidationError

from ...app.validators import AppURLValidator
from ..error_codes import AppErrorCode
from ..manifest_validations import validate_required_saleor_version

SALEOR_VERSION = "3.12.1"


def test_validate_url():
    url_validator = AppURLValidator()
    url = "http://otherapp:3000"
    assert url_validator(url) is None


def test_validate_invalid_url():
    url_validator = AppURLValidator()
    url = "otherapp:3000"
    with pytest.raises(ValidationError):
        url_validator(url)


@pytest.mark.parametrize(
    "required_version",
    [
        None,
        "*",
        "^3.11",
        "3.*",
        "3.12.x",
        ">3.12.0-a+build.1",
        "<=3.12",
        "^3.10 || ^3.12",
        "3.10 - 3.12",
    ],
)
def test_validate_required_saleor_version(required_version):
    assert validate_required_saleor_version(required_version, SALEOR_VERSION) is True


def test_validate_required_saleor_version_when_unsupported():
    with pytest.raises(ValidationError) as error:
        validate_required_saleor_version("~3.11 || >=3.13", SALEOR_VERSION)
    assert error.value.code == AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value


def test_validate_required_saleor_version_with_invalid_specification():
    with pytest.raises(ValidationError) as error:
        validate_required_saleor_version("invalid_range")
    assert error.value.code == AppErrorCode.INVALID.value
