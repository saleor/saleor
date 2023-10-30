from fnmatch import fnmatchcase
from typing import cast

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGISendEvent,
    HTTPResponseBodyEvent,
    HTTPResponseStartEvent,
    HTTPScope,
    Scope,
)
from django.conf import settings


def cors_handler(application: ASGI3Application) -> ASGI3Application:
    async def cors_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        # handle CORS preflight requests
        if scope["type"] != "http":
            await application(scope, receive, send)
            return
        # determine the origin of the request
        request_origin: str = ""
        for header, value in scope.get("headers", []):
            if header == b"origin":
                request_origin = value.decode("latin1")
        # if the origin is allowed, add the appropriate CORS headers
        origin_match = False
        if request_origin:
            for allowed_origin in settings.ALLOWED_GRAPHQL_ORIGINS:
                if fnmatchcase(request_origin, allowed_origin):
                    origin_match = True
                    break
        if scope["method"] == "OPTIONS":
            scope = cast(HTTPScope, scope)
            response_headers: list[tuple[bytes, bytes]] = [
                (b"access-control-allow-credentials", b"true"),
                (
                    b"access-control-allow-headers",
                    b"Origin, Content-Type, Accept, Authorization, "
                    b"Authorization-Bearer",
                ),
                (b"access-control-allow-methods", b"POST, OPTIONS"),
                (b"access-control-max-age", b"600"),
                (b"vary", b"Origin"),
            ]
            if origin_match:
                response_headers.append(
                    (
                        b"access-control-allow-origin",
                        request_origin.encode("latin1"),
                    )
                )
            await send(
                HTTPResponseStartEvent(
                    type="http.response.start",
                    status=200 if origin_match else 400,
                    headers=sorted(response_headers),
                    trailers=False,
                )
            )
            await send(
                HTTPResponseBodyEvent(
                    type="http.response.body", body=b"", more_body=False
                )
            )
        else:

            async def send_with_origin(message: ASGISendEvent) -> None:
                if message["type"] == "http.response.start":
                    response_headers = [
                        (key, value)
                        for key, value in message["headers"]
                        if key.lower()
                        not in {
                            b"access-control-allow-credentials",
                            b"access-control-allow-origin",
                            b"vary",
                        }
                    ]
                    response_headers.append(
                        (b"access-control-allow-credentials", b"true")
                    )
                    vary_header = next(
                        (
                            value
                            for key, value in message["headers"]
                            if key.lower() == b"vary"
                        ),
                        b"",
                    )
                    if origin_match:
                        response_headers.append(
                            (
                                b"access-control-allow-origin",
                                request_origin.encode("latin1"),
                            )
                        )
                        if b"Origin" not in vary_header:
                            if vary_header:
                                vary_header += b", Origin"
                            else:
                                vary_header = b"Origin"
                    if vary_header:
                        response_headers.append((b"vary", vary_header))
                    message["headers"] = sorted(response_headers)
                await send(message)

            await application(scope, receive, send_with_origin)

    return cors_wrapper
