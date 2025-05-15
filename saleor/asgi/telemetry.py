import os

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

from ..core.telemetry import saleor_attributes, set_global_attributes


def get_hostname(scope: Scope) -> str:
    if scope["type"] == "http":
        for header, value in scope["headers"]:
            if header.lower() == b"host":
                return value.decode("ascii").strip().lower()
    return ""


def telemetry_middleware(application: ASGI3Application) -> ASGI3Application:
    if os.environ.get("TELEMETRY_OTEL_INSTRUMENT", "").lower() == "true":
        application = OpenTelemetryMiddleware(application)  # type: ignore[assignment]

    async def telemetry_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        with set_global_attributes(
            {saleor_attributes.SALEOR_ENVIRONMENT_DOMAIN: get_hostname(scope)}
        ):
            return await application(scope, receive, send)

    return telemetry_wrapper
