from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)

from ..core.telemetry import set_global_attributes
from ..core.telemetry.attributes import SALEOR_ENVIRONMENT_DOMAIN


def get_hostname(scope: Scope) -> str:
    if scope["type"] == "http":
        for header, value in scope["headers"]:
            if header.lower() == b"host":
                return value.decode("ascii").strip().lower()
    return ""


def telemetry_middleware(application: ASGI3Application) -> ASGI3Application:
    async def telemetry_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        with set_global_attributes({SALEOR_ENVIRONMENT_DOMAIN: get_hostname(scope)}):
            return await application(scope, receive, send)

    return telemetry_wrapper
