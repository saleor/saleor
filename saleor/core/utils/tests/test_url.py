from collections import OrderedDict
from urllib.parse import urlencode

import pytest
from django.conf import settings

from ..url import get_default_storage_root_url, prepare_url, sanitize_url_for_logging


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


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://example.com/test", "http://example.com/test"),
        (
            "https://example.com:8000/test/path?q=val&k=val",
            "https://example.com:8000/test/path?q=val&k=val",
        ),
        ("https://user@example.com/test", "https://***:***@example.com/test"),
        ("https://:password@example.com/test", "https://***:***@example.com/test"),
        (
            "http://user:password@example.com:8000/test",
            "http://***:***@example.com:8000/test",
        ),
        (
            "awssqs://key:secret@sqs.us-east-2.amazonaws.com/xxxx/myqueue.fifo",
            "awssqs://***:***@sqs.us-east-2.amazonaws.com/xxxx/myqueue.fifo",
        ),
    ],
)
def test_sanitize_url_for_logging(url, expected):
    assert sanitize_url_for_logging(url) == expected
