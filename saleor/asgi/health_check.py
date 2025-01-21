from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    Scope,
)


def health_check(application: ASGI3Application, health_url: str) -> ASGI3Application:
    async def health_check_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope.get("type") != "http" or scope.get("path") != health_url:
            return await application(scope, receive, send)
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
        return None

    return health_check_wrapper
