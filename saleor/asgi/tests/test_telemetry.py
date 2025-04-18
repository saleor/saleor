from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asgiref.typing import ASGIReceiveCallable, ASGISendCallable

from ...asgi.telemetry import get_hostname, telemetry_middleware
from ...core.telemetry.saleor_attributes import SALEOR_ENVIRONMENT_DOMAIN


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        ({"type": "http", "headers": [(b"host", b"example.com")]}, "example.com"),
        (
            {"type": "http", "headers": [(b"host", b"example.com:8000")]},
            "example.com:8000",
        ),
        ({"type": "http", "headers": [(b"HOST", b"EXAMPLE.COM")]}, "example.com"),
    ],
)
def test_get_hostname_with_http_request(scope, expected):
    # when
    result = get_hostname(scope)  # type: ignore[call-arg]

    # then
    assert result == expected


def test_get_hostname_with_non_http_request():
    # given
    scope = {
        "type": "websocket",
        "headers": [
            (b"host", b"example.com"),
        ],
    }

    # when
    result = get_hostname(scope)  # type: ignore[call-arg]

    # then
    assert result == ""


def test_get_hostname_with_no_host_header():
    # given
    scope = {
        "type": "http",
        "headers": [
            (b"content-type", b"application/json"),
        ],
    }

    # when
    result = get_hostname(scope)  # type: ignore[call-arg]

    # then
    assert result == ""


@pytest.mark.asyncio
@patch("saleor.asgi.telemetry.set_global_attributes")
async def test_telemetry_middleware(mock_set_global_attrs):
    # given
    mock_set_global_attrs.return_value = MagicMock()
    mock_app = AsyncMock(return_value=None)

    scope = {
        "type": "http",
        "headers": [
            (b"host", b"example.com"),
        ],
    }
    receive = MagicMock(spec=ASGIReceiveCallable)
    send = MagicMock(spec=ASGISendCallable)

    # when
    middleware = telemetry_middleware(mock_app)
    await middleware(scope, receive, send)  # type: ignore[call-arg]

    # then
    mock_set_global_attrs.assert_called_once()
    assert SALEOR_ENVIRONMENT_DOMAIN in mock_set_global_attrs.call_args[0][0]
    assert (
        mock_set_global_attrs.call_args[0][0][SALEOR_ENVIRONMENT_DOMAIN]
        == "example.com"
    )

    # verify that the wrapped application was called with the same arguments
    mock_app.assert_called_once_with(scope, receive, send)
