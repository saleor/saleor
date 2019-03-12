import logging

from django.conf import settings
# from django_countries.fields import Country
#
# from .utils import get_currency_for_country

logger = logging.getLogger(__name__)


class CurrencyMiddleware(object):

    def process_request(self, request):
        # if hasattr(request, 'country') and request.country is not None:
        #     request.currency = get_currency_for_country(request.country)
        # else:
        request.currency = settings.DEFAULT_CURRENCY
