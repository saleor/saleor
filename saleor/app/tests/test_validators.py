import pytest
from django.core.exceptions import ValidationError

from ... import __version__
from ...app.validators import AppURLValidator
from ..error_codes import AppErrorCode
from ..manifest_validations import (
    VersionConstraint,
    parse_version,
    validate_required_saleor_version,
)


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
        ("3.10.x || 3.12.*", "3.11.5", False),
        ("^3.12", "4.0.0", False),
        ("^3.12", "3.12.0-a", False),
    ],
)
def test_version_constraint(required_version, version, satisfied):
    constraint = VersionConstraint(required_version, version)
    assert constraint.constraint == required_version
    assert constraint.satisfied == satisfied


@pytest.mark.parametrize(
    "required_version", ["3.8-3.9", "^3w.11", {"wrong", "data type"}, 12, 0.5, None]
)
def test_version_constraint_with_invalid_range(required_version):
    with pytest.raises(ValueError):
        VersionConstraint(required_version, "3.12.1")


def test_validate_required_saleor_version():
    with pytest.raises(ValidationError) as validation_error:
        validate_required_saleor_version(VersionConstraint("^3.13", "3.12.1"))
    errors = validation_error.value.error_dict["requiredSaleorVersion"]
    assert len(errors) == 1
    assert errors[0].code == AppErrorCode.UNSUPPORTED_SALEOR_VERSION.value
    assert validate_required_saleor_version(None) is True
