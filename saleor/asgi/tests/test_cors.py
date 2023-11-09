import pytest
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPScope,
)

from ..cors_handler import cors_handler

ACCESS_CONTROL_ALLOW_ORIGIN = "Access-Control-Allow-Origin"
ACCESS_CONTROL_ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
ACCESS_CONTROL_ALLOW_HEADERS = "Access-Control-Allow-Headers"
ACCESS_CONTROL_ALLOW_METHODS = "Access-Control-Allow-Methods"


def build_scope(origin: str, method: str) -> HTTPScope:
    return {
        "type": "http",
        "asgi": {"spec_version": "2.1", "version": "3.0"},
        "http_version": "2",
        "method": method,
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"hostname", b"localhost:3000"),
            (b"origin", origin.encode("latin1")),
        ],
        "client": ("127.0.0.1", 80),
        "server": None,
        "extensions": {},
    }


async def run_app(app: ASGI3Application, scope: HTTPScope) -> list[dict]:
    events = []

    async def send(event) -> None:
        events.append(event)

    async def receive() -> ASGIReceiveEvent:
        raise NotImplementedError()

    await app(scope, receive, send)
    return events


async def test_access_control_header_preflight(asgi_app: ASGI3Application, settings):
    settings.ALLOWED_GRAPHQL_ORIGINS = ["*"]
    cors_app = cors_handler(asgi_app)
    events = await run_app(cors_app, build_scope("http://localhost:3000", "OPTIONS"))
    assert events == [
        HTTPResponseStartEvent(
            type="http.response.start",
            status=200,
            headers=[
                (b"access-control-allow-credentials", b"true"),
                (
                    b"access-control-allow-headers",
                    b"Origin, Content-Type, Accept, Authorization, "
                    b"Authorization-Bearer",
                ),
                (b"access-control-allow-methods", b"POST, OPTIONS"),
                (b"access-control-allow-origin", b"http://localhost:3000"),
                (b"access-control-max-age", b"600"),
                (b"vary", b"Origin"),
            ],
            trailers=False,
        ),
        HTTPResponseBodyEvent(type="http.response.body", body=b"", more_body=False),
    ]


async def test_access_control_header_simple(asgi_app: ASGI3Application, settings):
    settings.ALLOWED_GRAPHQL_ORIGINS = ["*"]
    cors_app = cors_handler(asgi_app)
    events = await run_app(cors_app, build_scope("http://localhost:3000", "POST"))
    assert events == [
        HTTPResponseStartEvent(
            type="http.response.start",
            status=200,
            headers=[
                (b"access-control-allow-credentials", b"true"),
                (b"access-control-allow-origin", b"http://localhost:3000"),
                (b"content-type", b"text/plain"),
                (b"vary", b"Origin"),
            ],
            trailers=False,
        ),
        HTTPResponseBodyEvent(type="http.response.body", body=b"", more_body=False),
    ]


@pytest.mark.parametrize(
    ("allowed_origins", "origin"),
    [
        (["*"], "http://example.org"),
        (["*"], "https://example.org"),
        (["*"], "http://localhost:3000"),
        (["*"], "http://localhost:9000"),
        (["*"], "file://"),
        (["http://example.org"], "http://example.org"),
        (["http://example.org", "https://example.org"], "http://example.org"),
        (["http://example.org", "https://example.org"], "https://example.org"),
        (["https://*.example.org"], "https://api.example.org"),
    ],
)
async def test_access_control_allowed_origins(
    asgi_app, settings, allowed_origins, origin
):
    settings.ALLOWED_GRAPHQL_ORIGINS = allowed_origins
    cors_app = cors_handler(asgi_app)
    events = await run_app(cors_app, build_scope(origin, "OPTIONS"))
    assert events[0]["type"] == "http.response.start"
    assert events[0]["status"] == 200
    assert (b"access-control-allow-origin", origin.encode("latin1")) in events[0][
        "headers"
    ]


@pytest.mark.parametrize(
    ("allowed_origins", "origin"),
    [
        (["http://example.org"], "https://example.org"),
        (["http://example.org"], "http://localhost:3000"),
        (["http://example.org"], "file://example.org"),
        (["http://example.org"], "http://example.org:8000"),
        (["http://example.org", "https://example.org"], "http://api.example.org"),
        (["https://*.example.org"], "https://apiexample.com"),
    ],
)
async def test_access_control_disallowed_origins(
    asgi_app, settings, allowed_origins, origin
):
    settings.ALLOWED_GRAPHQL_ORIGINS = allowed_origins
    cors_app = cors_handler(asgi_app)
    events = await run_app(cors_app, build_scope(origin, "OPTIONS"))
    assert events[0]["type"] == "http.response.start"
    assert events[0]["status"] == 400
    assert (b"access-control-allow-origin", origin.encode("latin1")) not in events[0][
        "headers"
    ]
