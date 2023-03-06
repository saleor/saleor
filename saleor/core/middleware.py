import logging
from datetime import datetime
from typing import TYPE_CHECKING, Union

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.translation import get_language

from . import analytics
from .jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, jwt_decode_with_exception_handler

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App

Requestor = Union["User", "App"]

logger = logging.getLogger(__name__)


def google_analytics(get_response):
    """Report a page view to Google Analytics."""

    if not settings.GOOGLE_ANALYTICS_TRACKING_ID:
        raise MiddlewareNotUsed()

    def _google_analytics_middleware(request):
        client_id = analytics.get_client_id(request)
        path = request.path
        language = get_language()
        headers = request.META
        try:
            analytics.report_view(
                client_id, path=path, language=language, headers=headers
            )
        except Exception:
            logger.exception("Unable to update analytics")
        return get_response(request)

    return _google_analytics_middleware


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
