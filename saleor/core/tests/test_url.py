from urllib.parse import urlencode

from ..utils.url import prepare_url


def test_prepare_url():
    redirect_url = "https://www.example.com"
    params = urlencode({"param1": "abc", "param2": "xyz"})
    result = prepare_url(params, redirect_url)
    assert result == "https://www.example.com?param1=abc&param2=xyz"
