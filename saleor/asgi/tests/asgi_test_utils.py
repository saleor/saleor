from asgiref.typing import Scope, WebSocketScope
from django.core.handlers.asgi import ASGIHandler


class DummyASGIApplication(ASGIHandler):
    """A dummy ASGI application that always return a dummy string.

    Used to indicate it was called successfully.
    """

    RESPONSE_STRING = "Dummy ASGI Application: called."

    async def __call__(self, scope: Scope, receive, send):
        return self.RESPONSE_STRING


def create_asgi_scope_websocket_proto(
    path: str, headers: list[tuple[bytes, bytes] | None] = None
) -> WebSocketScope:
    """Return a webhook protocol ASGI 3.0 scope."""
    return {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "path": path,  # str
        # raw_path: the original HTTP path (w/o query string), unmodified from what was
        # received by the web server. Optional (nullable).
        "raw_path": path,
        # The root path this application is mounted at.
        "root_path": None,
        "headers": headers or [],
        "client": ("127.0.0.1", 0),
        "server": ("testserver", "80"),
        "subprotocols": [],
        "state": {},
        "extensions": None,
    }
