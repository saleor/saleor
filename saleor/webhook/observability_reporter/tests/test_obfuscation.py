import pytest

from ..obfuscation import MASK, hide_sensitive_headers


@pytest.mark.parametrize(
    "headers,sensitive,expected",
    [
        (
            {"header1": "text", "header2": "text"},
            ("AUTHORIZATION", "AUTHORIZATION_BEARER"),
            {"header1": "text", "header2": "text"},
        ),
        (
            {"header1": "text", "authorization": "secret"},
            ("AUTHORIZATION", "AUTHORIZATION_BEARER"),
            {"header1": "text", "authorization": MASK},
        ),
        (
            {"HEADER1": "text", "authorization-bearer": "secret"},
            ("AUTHORIZATION", "AUTHORIZATION_BEARER"),
            {"HEADER1": "text", "authorization-bearer": MASK},
        ),
    ],
)
def test_hide_sensitive_headers(headers, sensitive, expected):
    assert hide_sensitive_headers(headers, sensitive_headers=sensitive) == expected
