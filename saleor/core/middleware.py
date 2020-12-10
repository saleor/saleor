import logging
from datetime import datetime

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import MiddlewareNotUsed
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.translation import get_language
from django_countries.fields import Country

from ..discount.utils import fetch_discounts
from ..plugins.manager import get_plugins_manager
from . import analytics
from .jwt import JWT_REFRESH_TOKEN_COOKIE_NAME, jwt_decode
from .utils import get_client_ip, get_country_by_ip, get_currency_for_country

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


def request_time(get_response):
    def _stamp_request(request):
        request.request_time = timezone.now()
        return get_response(request)

    return _stamp_request


def discounts(get_response):
    """Assign active discounts to `request.discounts`."""

    def _discounts_middleware(request):
        request.discounts = SimpleLazyObject(
            lambda: fetch_discounts(request.request_time)
        )
        return get_response(request)

    return _discounts_middleware


def country(get_response):
    """Detect the user's country and assign it to `request.country`."""

    def _country_middleware(request):
        client_ip = get_client_ip(request)
        if client_ip:
            request.country = get_country_by_ip(client_ip)
        if not request.country:
            request.country = Country(settings.DEFAULT_COUNTRY)
        return get_response(request)

    return _country_middleware


def currency(get_response):
    """Take a country and assign a matching currency to `request.currency`."""

    def _currency_middleware(request):
        if hasattr(request, "country") and request.country is not None:
            request.currency = get_currency_for_country(request.country)
        return get_response(request)

    return _currency_middleware


def site(get_response):
    """Clear the Sites cache and assign the current site to `request.site`.

    By default django.contrib.sites caches Site instances at the module
    level. This leads to problems when updating Site instances, as it's
    required to restart all application servers in order to invalidate
    the cache. Using this middleware solves this problem.
    """

    def _get_site():
        Site.objects.clear_cache()
        return Site.objects.get_current()

    def _site_middleware(request):
        request.site = SimpleLazyObject(_get_site)
        return get_response(request)

    return _site_middleware


def plugins(get_response):
    """Assign plugins manager."""

    def _get_manager():
        return get_plugins_manager(plugins=settings.PLUGINS)

    def _plugins_middleware(request):
        request.plugins = SimpleLazyObject(lambda: _get_manager())
        return get_response(request)

    return _plugins_middleware


def jwt_refresh_token_middleware(get_response):
    def middleware(request):
        """Append generated refresh_token to response object."""
        response = get_response(request)
        jwt_refresh_token = getattr(request, "refresh_token", None)
        if jwt_refresh_token:
            expires = None
            if settings.JWT_EXPIRE:
                refresh_token_payload = jwt_decode(jwt_refresh_token)
                expires = datetime.utcfromtimestamp(refresh_token_payload["exp"])
            response.set_cookie(
                JWT_REFRESH_TOKEN_COOKIE_NAME,
                jwt_refresh_token,
                expires=expires,
                httponly=True,  # protects token from leaking
                secure=not settings.DEBUG,
            )
        return response

    return middleware
