import logging
from datetime import datetime
from typing import TYPE_CHECKING, Union

from django.conf import settings

from .jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, jwt_decode_with_exception_handler

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App

Requestor = Union["User", "App"]

logger = logging.getLogger(__name__)


def jwt_refresh_token_middleware(get_response):
    def middleware(request):
        """Append generated refresh_token to response object."""
        response = get_response(request)
        jwt_refresh_token = getattr(request, "refresh_token", None)
        if jwt_refresh_token:
            expires = None
            secure = not settings.DEBUG
            if settings.JWT_EXPIRE:
                refresh_token_payload = jwt_decode_with_exception_handler(
                    jwt_refresh_token
                )
                if refresh_token_payload and refresh_token_payload.get("exp"):
                    expires = datetime.utcfromtimestamp(refresh_token_payload["exp"])
            response.set_cookie(
                JWT_REFRESH_TOKEN_COOKIE_NAME,
                jwt_refresh_token,
                expires=expires,
                httponly=True,  # protects token from leaking
                secure=secure,
                samesite="None" if secure else "Lax",
            )
        return response

    return middleware
