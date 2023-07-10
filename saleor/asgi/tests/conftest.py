import pytest
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    Scope,
)


@pytest.fixture
def asgi_app() -> ASGI3Application:
    async def fake_app(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        await send(
            HTTPResponseStartEvent(
                type="http.response.start",
                status=200,
                headers=[(b"content-type", b"text/plain")],
                trailers=False,
            )
        )
        await send(
            HTTPResponseBodyEvent(type="http.response.body", body=b"", more_body=False)
        )

    return fake_app


@pytest.fixture
def large_asgi_app() -> ASGI3Application:
    async def fake_app(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        await send(
            HTTPResponseStartEvent(
                type="http.response.start",
                status=200,
                headers=[
                    (b"content-length", b"10000"),
                    (b"content-type", b"text/plain"),
                ],
                trailers=False,
            )
        )
        await send(
            HTTPResponseBodyEvent(
                type="http.response.body", body=10000 * b"x", more_body=False
            )
        )

    return fake_app
