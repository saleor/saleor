from collections import OrderedDict
from urllib.parse import urlencode

from django.conf import settings

from ..url import get_default_storage_root_url, prepare_url


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


def test_get_default_storage_root_url(site_settings):
    # when
    root_url = get_default_storage_root_url()

    # then
    assert root_url == f"http://{site_settings.site.domain}{settings.MEDIA_URL}"
