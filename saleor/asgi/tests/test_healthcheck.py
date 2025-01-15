from unittest import mock

from saleor.asgi import health_check
from saleor.asgi.tests.asgi_test_utils import (
    DummyASGIApplication,
    create_asgi_scope_websocket_proto,
)


async def test_non_http_requests_forwarded_to_next_wrapper():
    """Ensure the middleware forwards the request when the protocol isn't HTTP."""

    scope = create_asgi_scope_websocket_proto("/health/")
    handler = health_check(DummyASGIApplication(), health_url="/health/")

    # WebSocket protocol shouldn't return an empty response (healthcheck),
    # instead it should return the dummy response from the dummy ASGI application.
    response = await handler(scope, receive=None, send=None)
    assert response == DummyASGIApplication.RESPONSE_STRING

    # When protocol is HTTP, it should return the health check result
    # (HTTP 200 + empty body) instead of the dummy response (i.e., shouldn't forward the
    # request down the chain).
    scope["type"] = "http"
    send_callback = mock.AsyncMock()
    response = await handler(scope, receive=None, send=send_callback)
    # Shouldn't have returned anything (especially not the string from
    # DummyASGIApplication.RESPONSE_STRING)
    assert response is None
    assert send_callback.call_args_list == [
        mock.call(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
                "trailers": False,
            }
        ),
        mock.call(
            {
                "type": "http.response.body",
                "body": b"",
                "more_body": False,
            }
        ),
    ]
