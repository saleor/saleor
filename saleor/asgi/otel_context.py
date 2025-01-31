from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)
from opentelemetry.semconv.attributes.server_attributes import SERVER_ADDRESS

from ..core.otel.context import set_trace_attributes


def get_hostname(scope: Scope) -> str:
    hostname: str = ""
    if scope["type"] == "http":
        for header, value in scope["headers"]:
            if header == b"host":
                hostname = value.decode("latin1")
                break
    hostname = hostname.split(":")[0]  # remove port
    hostname = hostname.removeprefix("www.")
    return hostname.lower()


def otel_context(application: ASGI3Application) -> ASGI3Application:
    async def otel_context_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        with set_trace_attributes({SERVER_ADDRESS: get_hostname(scope)}):
            return await application(scope, receive, send)

    return otel_context_wrapper
