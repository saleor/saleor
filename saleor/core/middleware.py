import logging

from django.conf import settings
from django.utils.translation import get_language
from django_countries.fields import Country

from .utils import get_currency_for_country
from ..discount.models import Sale

logger = logging.getLogger(__name__)


class CountryMiddleware(object):

    def process_request(self, request):
        # if client_ip:
        #     request.country = get_country_by_ip(client_ip)
        if not getattr(request, 'country', None):
            request.country = Country(settings.DEFAULT_COUNTRY)


class CurrencyMiddleware(object):

    def process_request(self, request):
        if hasattr(request, 'country') and request.country is not None:
            request.currency = get_currency_for_country(request.country)
        else:
            request.currency = settings.DEFAULT_CURRENCY
