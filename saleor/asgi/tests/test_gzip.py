import gzip
from typing import List

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPScope,
)

from ..gzip_compression import gzip_compression


def build_scope(origin: str, encodings: bytes) -> HTTPScope:
    return {
        "type": "http",
        "asgi": {"spec_version": "2.1", "version": "3.0"},
        "http_version": "2",
        "method": "OPTIONS",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"accept-encoding", encodings),
            (b"hostname", b"localhost:3000"),
            (b"origin", origin.encode("latin1")),
        ],
        "client": ("127.0.0.1", 80),
        "server": None,
        "extensions": {},
    }


async def run_app(app: ASGI3Application, scope: HTTPScope) -> List[dict]:
    events = []

    async def send(event) -> None:
        events.append(event)

    async def receive() -> ASGIReceiveEvent:
        raise NotImplementedError()

    await app(scope, receive, send)
    return events


async def test_no_compression(large_asgi_app: ASGI3Application, settings):
    settings.ALLOWED_GRAPHQL_ORIGINS = ["*"]
    cors_app = gzip_compression(large_asgi_app)
    events = await run_app(cors_app, build_scope("http://localhost:3000", b"identity"))
    assert events == [
        HTTPResponseStartEvent(
            type="http.response.start",
            status=200,
            headers=[
                (b"content-length", b"10000"),
                (b"content-type", b"text/plain"),
            ],
            trailers=False,
        ),
        HTTPResponseBodyEvent(
            type="http.response.body", body=10000 * b"x", more_body=False
        ),
    ]


async def test_with_supported_compression(large_asgi_app: ASGI3Application, settings):
    settings.ALLOWED_GRAPHQL_ORIGINS = ["*"]
    cors_app = gzip_compression(large_asgi_app)
    events = await run_app(cors_app, build_scope("http://localhost:3000", b"gzip"))
    expected_payload = gzip.compress(10000 * b"x", compresslevel=9)
    assert events == [
        HTTPResponseStartEvent(
            type="http.response.start",
            status=200,
            headers=[
                (b"content-type", b"text/plain"),
                (b"content-encoding", b"gzip"),
                (b"content-length", str(len(expected_payload)).encode("latin1")),
            ],
            trailers=False,
        ),
        HTTPResponseBodyEvent(
            type="http.response.body", body=expected_payload, more_body=False
        ),
    ]
