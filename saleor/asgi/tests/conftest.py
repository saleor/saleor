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
            )
        )
        await send(
            HTTPResponseBodyEvent(type="http.response.body", body=b"", more_body=False)
        )

    return fake_app
