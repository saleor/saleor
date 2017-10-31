import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.translation import get_language
from django_countries.fields import Country

from . import analytics
from ..discount.models import Sale
from .utils import get_client_ip, get_country_by_ip, get_currency_for_country

logger = logging.getLogger(__name__)


class GoogleAnalytics(object):
    def process_request(self, request):
        client_id = analytics.get_client_id(request)
        path = request.path
        language = get_language()
        headers = request.META
        # FIXME: on production you might want to run this in background
        try:
            analytics.report_view(client_id, path=path, language=language,
                                  headers=headers)
        except Exception:
            logger.exception('Unable to update analytics')


class DiscountMiddleware(object):
    def process_request(self, request):
        discounts = Sale.objects.all()
        discounts = discounts.prefetch_related('products', 'categories')
        request.discounts = discounts


class CountryMiddleware(object):

    def process_request(self, request):
        client_ip = get_client_ip(request)
        if client_ip:
            request.country = get_country_by_ip(client_ip)
        if not request.country:
            request.country = Country(settings.DEFAULT_COUNTRY)


class CurrencyMiddleware(object):

    def process_request(self, request):
        if hasattr(request, 'country') and request.country is not None:
            request.currency = get_currency_for_country(request.country)
        else:
            request.currency = settings.DEFAULT_CURRENCY


class ClearSiteCacheMiddleware(object):
    """
    This middleware clears the Sites cache, refetches the current Site
    and sets it as attribute in request object for future uses in this
    request cycle.
    By default django.contrib.sites caches Site instances at the module
    level, which leads to problems when updating Site instances, such
    as necessity to restart the application server in order to invalidate
    the cache. Using this middleware solves this problem.
    """

    def process_request(self, request):
        Site.objects.clear_cache()
        request.site = Site.objects.get_current()
