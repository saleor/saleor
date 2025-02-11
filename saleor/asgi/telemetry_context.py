from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)

from ..core.telemetry import SpanAttributes, set_global_attributes


def get_hostname(scope: Scope) -> str:
    hostname: str = ""
    if scope["type"] == "http":
        for header, value in scope["headers"]:
            if header.lower() == b"host":
                hostname = value.decode("utf-8")
                break
    return hostname.lower()


def telemetry_context(application: ASGI3Application) -> ASGI3Application:
    async def telemetry_context_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        with set_global_attributes(
            {SpanAttributes.SERVER_ADDRESS: get_hostname(scope)}
        ):
            return await application(scope, receive, send)

    return telemetry_context_wrapper
