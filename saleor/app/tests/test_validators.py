import pytest
from django.core.exceptions import ValidationError

from ...app.validators import AppURLValidator


def test_validate_url():
    url_validator = AppURLValidator()
    url = "http://otherapp:3000"
    assert url_validator(url) is None


def test_validate_invalid_url():
    url_validator = AppURLValidator()
    url = "otherapp:3000"
    with pytest.raises(ValidationError):
        url_validator(url)
