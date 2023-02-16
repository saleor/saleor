# adapted from Starlette's GZipMiddleware
# Starlette does not work with Django's case-sensitive headers

import gzip
import io
from typing import Optional

from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGISendEvent,
    HTTPResponseStartEvent,
    Scope,
)


def gzip_compression(
    app: ASGI3Application, minimum_size: int = 500, compresslevel: int = 9
) -> ASGI3Application:
    async def gzip_compression_wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope["type"] == "http":
            accepted_encoding = next(
                (
                    value
                    for key, value in scope["headers"]
                    if key.lower() == b"accept-encoding"
                ),
                b"",
            )
            if b"gzip" in accepted_encoding:
                start_message: Optional[HTTPResponseStartEvent] = None
                content_encoding_set = False
                started = False
                gzip_buffer = io.BytesIO()
                gzip_file = gzip.GzipFile(
                    mode="wb", fileobj=gzip_buffer, compresslevel=compresslevel
                )

                async def send_compressed(message: ASGISendEvent) -> None:
                    nonlocal content_encoding_set
                    nonlocal start_message
                    nonlocal started
                    if message["type"] == "http.response.start":
                        start_message = message
                        headers = start_message["headers"]
                        content_encoding_set = any(
                            value
                            for key, value in headers
                            if key.lower() == b"content-encoding"
                        )
                    elif (
                        message["type"] == "http.response.body" and content_encoding_set
                    ):
                        if not started:
                            assert start_message is not None
                            started = True
                            await send(start_message)
                        await send(message)
                    elif message["type"] == "http.response.body" and not started:
                        assert start_message is not None
                        started = True
                        body = message.get("body", b"")
                        more_body = message.get("more_body", False)
                        if len(body) < minimum_size and not more_body:
                            # Don't apply GZip to small outgoing responses.
                            await send(start_message)
                            await send(message)
                        elif not more_body:
                            # Standard GZip response.
                            gzip_file.write(body)
                            gzip_file.close()
                            body = gzip_buffer.getvalue()

                            headers = start_message["headers"]
                            headers = [
                                (key, value)
                                for key, value in headers
                                if key.lower()
                                not in (b"content-length", b"content-encoding")
                            ]
                            headers.append((b"content-encoding", b"gzip"))
                            headers.append(
                                (
                                    b"content-length",
                                    str(len(body)).encode("latin-1"),
                                )
                            )
                            for key, value in headers:
                                if key.lower() == b"vary":
                                    if b"Accept-Encoding" not in value:
                                        value += b", Accept-Encoding"
                                        break
                            start_message["headers"] = headers

                            message["body"] = body

                            await send(start_message)
                            await send(message)
                        else:
                            # Initial body in streaming GZip response.
                            headers = start_message["headers"]
                            headers = [
                                (key, value)
                                for key, value in headers
                                if key.lower()
                                not in (b"content-length", b"content-encoding")
                            ]
                            headers.append((b"content-encoding", b"gzip"))
                            for key, value in headers:
                                if key.lower() == b"vary":
                                    if b"Accept-Encoding" not in value:
                                        value += b", Accept-Encoding"
                                        break
                            start_message["headers"] = headers

                            gzip_file.write(body)
                            message["body"] = gzip_buffer.getvalue()
                            gzip_buffer.seek(0)
                            gzip_buffer.truncate()

                            await send(start_message)
                            await send(message)

                    elif message["type"] == "http.response.body":
                        # Remaining body in streaming GZip response.
                        body = message.get("body", b"")
                        more_body = message.get("more_body", False)

                        gzip_file.write(body)
                        if not more_body:
                            gzip_file.close()

                        message["body"] = gzip_buffer.getvalue()
                        gzip_buffer.seek(0)
                        gzip_buffer.truncate()

                        await send(message)

                await app(scope, receive, send_compressed)
                return
        await app(scope, receive, send)

    return gzip_compression_wrapper
