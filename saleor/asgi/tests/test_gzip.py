import gzip
from unittest import mock

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


async def run_app(app: ASGI3Application, scope: HTTPScope) -> list[dict]:
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

    with mock.patch(
        # Returns an empty 'random' filename in order to make the HTTP response
        # predictable for this test case
        "saleor.asgi.gzip_compression._get_random_filename",
        wraps=lambda: "",
    ):
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


async def test_response_content_length_includes_random_filename(
    large_asgi_app: ASGI3Application,
):
    """Ensure the response contains a random filename when compressed.

    This is done by mocking the random number generator so that it always returns
    a random 8 bytes filename (meaning it always returns `xxxxxxxx` as the random
    filename), then we check that this random filename is present in the HTTP
    response as well as in the `content-length` header.
    """

    cors_app = gzip_compression(large_asgi_app)

    dummy_random_filename_length = 8
    expected_random_filename = b"x" * dummy_random_filename_length

    with mock.patch(
        "secrets.randbelow", wraps=lambda _upperbound: dummy_random_filename_length
    ):
        events = await run_app(cors_app, build_scope("http://localhost:3000", b"gzip"))

    assert len(events) == 2
    resp_event, body_event = events

    # Note: this is a TypeDict thus can't do `isinstance(..., HTTPResponseBodyEvent)`
    resp_event: HTTPResponseStartEvent
    assert resp_event["type"] == "http.response.start"

    body_event: HTTPResponseBodyEvent
    assert isinstance(body_event, dict)
    assert body_event["type"] == "http.response.body"

    resp_headers = dict(resp_event["headers"])
    assert resp_headers == {
        b"content-encoding": b"gzip",
        b"content-type": b"text/plain",
        b"content-length": str(
            # content-length should include the random filename
            len(gzip.compress(10000 * b"x", compresslevel=9))
            + dummy_random_filename_length
            + 1  # NUL (0x00) which separates the filename
        ).encode("latin1"),
    }

    body: bytes = body_event["body"]

    # Ensure this is a Gzip response (by checking the magic number)
    # and that it contains a filename
    # 1F 8B 08 08
    #          ^^
    #           |--> Means a filename is included
    #       ^^
    #        |-----> Means compression method is a deflate
    # ^^^^^
    #    |---------> Means this is a gzip file (magic number)
    assert body.startswith(b"\x1f\x8b\x08\x08"), "should be a gzip response w/ filename"

    # Ensure the body contains the random filename
    filename = body[10:]  # 4 + 6 bytes (magic number + 6 bytes separator)
    assert filename.startswith(expected_random_filename + b"\x00")


async def test_response_content_length_is_random(
    large_asgi_app: ASGI3Application,
):
    """Ensure the response is random when compressed.

    This is done by generating multiple responses, then getting the average value
    which should be a float rather than an integer which would indicate a constant
    content-length instead of being random.
    """

    cors_app = gzip_compression(large_asgi_app)

    async def _send_request() -> bytes:
        """Send a request and return the body."""

        events = await run_app(cors_app, build_scope("http://localhost:3000", b"gzip"))

        assert len(events) == 2
        resp_event, body_event = events

        resp_event: HTTPResponseStartEvent
        assert resp_event["type"] == "http.response.start"

        body_event: HTTPResponseBodyEvent
        assert isinstance(body_event, dict)
        assert body_event["type"] == "http.response.body"

        return body_event["body"]

    # Retrieves the length with a 1-byte filename
    with mock.patch("secrets.randbelow", wraps=lambda _upperbound: 1):
        body = await _send_request()

        # Should start with 1F 8B 8B 08 - meaning this is a deflate gzip file
        # with a filename
        assert body.startswith(b"\x1f\x8b\x08\x08")
        length_1byte_filename = len(body)

    lengths = []

    for _i in range(10):
        lengths.append(len(await _send_request()))

    # On average, the filename's length should be higher than 1 byte, and thus
    # on average it should exceed the length of 'length_1byte_filename'
    avg: float = sum(lengths) / float(len(lengths))
    assert avg > length_1byte_filename
