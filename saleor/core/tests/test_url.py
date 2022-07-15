from collections import OrderedDict
from urllib.parse import urlencode

from ..utils.url import prepare_url


def test_prepare_url():
    redirect_url = "https://www.example.com"
    params = urlencode({"param1": "abc", "param2": "xyz"})
    result = prepare_url(params, redirect_url)
    assert result == f"{redirect_url}?param1=abc&param2=xyz"


def test_prepare_url_with_existing_query():
    redirect_url = "https://www.example.com/?param=1&param=2"
    params = urlencode(OrderedDict({"param3": "abc", "param4": "xyz"}))
    result = prepare_url(params, redirect_url)
    assert result == f"{redirect_url}&param3=abc&param4=xyz"
