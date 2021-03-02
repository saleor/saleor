from urllib.parse import urlencode

import pytest
from django.core.exceptions import ValidationError

from ..utils.url import prepare_url, validate_url


def test_prepare_url():
    redirect_url = "https://www.example.com"
    params = urlencode({"param1": "abc", "param2": "xyz"})
    result = prepare_url(params, redirect_url)
    assert result == f"{redirect_url}?param1=abc&param2=xyz"


def test_validate_url():
    url = "http://otherapp:3000"
    result = validate_url(url)

    assert result == "otherapp"


def test_validate_invalid_url():
    url = "otherapp:3000"
    with pytest.raises(ValidationError):
        validate_url(url)
