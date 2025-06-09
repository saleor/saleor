import datetime
import logging
from typing import TYPE_CHECKING, Union

from django.conf import settings

from .jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, jwt_decode_with_exception_handler

import re
from django.utils.deprecation import MiddlewareMixin
from ..product.models import Product, ProductBrowsingHistory

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
                    expires = datetime.datetime.fromtimestamp(
                        refresh_token_payload["exp"], tz=datetime.UTC
                    )
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

class ProductViewTrackingMiddleware(MiddlewareMixin):
    """Middleware that tracks product page views"""
    
    # Product Page URL Pattern
    PRODUCT_URL_PATTERN = re.compile(r'/products/([^/]+)/?$')
    
    def process_response(self, request, response):
        """Process the response and check whether browsing needs to be recorded"""
        if response.status_code == 200:  # Only log successful requests
            self.maybe_record_product_view(request)
        return response
    
    def maybe_record_product_view(self, request):
        """Check and record product browsing"""
        # Check if it is a product page
        match = self.PRODUCT_URL_PATTERN.match(request.path)
        if not match:
            return
        
        product_slug = match.group(1)
        
        try:
            # Find products by slug
            product = Product.objects.get(slug=product_slug)
            
            # Record browsing
            user = request.user if request.user.is_authenticated else None
            session_key = request.session.session_key
            ip_address = self.get_client_ip(request)
            
            ProductBrowsingHistory.record_view(
                product=product,
                user=user,
                session_key=session_key,
                ip_address=ip_address
            )
            
        except Product.DoesNotExist:
            # The product does not exist
            pass
        except Exception:
            # When an error occurs, it does not affect the main process
            pass
    
    def get_client_ip(self, request):
        """Get the client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip