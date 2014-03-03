from __future__ import unicode_literals

import logging
import json

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
import requests
from purl import URL

from .models import RateSource, Rate


logger = logging.getLogger(__name__)


class RateBackendError(Exception):
    """
    Base exceptions raised by RateBackend implementations
    """


class BaseRateBackend(object):
    source_name = None
    base_currency = None

    def get_name(self):
        """
        Return the name that identifies the ratings source
        """
        if not self.source_name:
            raise RateBackendError("'source_name' can't be empty or"
                                   "you should override 'get_source_name'")

        return self.source_name

    def get_base_currency(self):
        """
        Return the base currency to which the rates are referred
        """
        if not self.base_currency:
            raise RateBackendError("'base_currency' can't be empty or"
                                   "you should override 'get_base_currency'")

        return self.base_currency

    def get_rates(self):
        """
        Return a dictionary that maps currency code with its rate value
        """
        raise NotImplementedError

    def update_rates(self):
        """
        Creates or updates rates for a source
        """
        source, created = RateSource.objects.get_or_create(
            name=self.get_name())
        source.base_currency = self.get_base_currency()
        source.save()

        for currency, value in self.get_rates().items():
            try:
                rate = Rate.objects.get(source=source, currency=currency)
            except Rate.DoesNotExist:
                rate = Rate(source=source, currency=currency)

            rate.value = value
            rate.save()


class OpenExchangeBackend(BaseRateBackend):
    source_name = "openexchange.org"

    def __init__(self):
        if not settings.OPENEXCHANGE["URL"]:
            raise ImproperlyConfigured("URL setting is empty")

        if not settings.OPENEXCHANGE["APP_ID"]:
            raise ImproperlyConfigured("APP_ID setting is empty")

        base_url = URL(settings.OPENEXCHANGE['URL'])
        parametrized_url = base_url.query_params({
             'app_id': settings.OPENEXCHANGE["APP_ID"],
             'base': self.get_base_currency()
        })

        self.url = parametrized_url.as_string()

    def get_rates(self):
        try:
            logger.debug("Connecting to url %s" % self.url)
            request = requests.get(self.url)
            return json.loads(request.content)['rates']

        except Exception as e:
            logger.exception("Error retrieving data from %s", self.url)
            raise RateBackendError("Error retrieving rates: %s" % e)

    def get_base_currency(self):
        return settings.OPENEXCHANGE["BASE_CURRENCY"]