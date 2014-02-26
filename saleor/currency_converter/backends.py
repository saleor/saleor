from __future__ import unicode_literals

import logging
import json

from django.core.exceptions import ImproperlyConfigured
from django.utils import six
from django.conf import settings
import requests

from .models import RateSource, Rate


logger = logging.getLogger(__name__)


class RateBackendError(Exception):
    """
    Base exceptions raised by RateBackend implementations
    """


class BaseRateBackend(object):
    source_name = None
    base_currency = None

    def get_source_name(self):
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
            name=self.get_source_name())
        source.base_currency = self.get_base_currency()
        source.save()

        for currency, value in six.iteritems(self.get_rates()):
            try:
                rate = Rate.objects.get(source=source, currency=currency)
            except Rate.DoesNotExist:
                rate = Rate(source=source, currency=currency)

            rate.value = value
            rate.save()


class OpenExchangeBackend(BaseRateBackend):
    source_name = "openexchange.org"

    def __init__(self):
        if not settings.CURRENCY_CONVERTER["OPENEXCHANGE_URL"]:
            raise ImproperlyConfigured("OPENEXCHANGE_URL setting is empty")

        if not settings.CURRENCY_CONVERTER["OPENEXCHANGE_APP_ID"]:
            raise ImproperlyConfigured("OPENEXCHANGE_APP_ID setting is empty")

        # Build the base api url
        base_url = "%s?app_id=%s" % (
            settings.CURRENCY_CONVERTER["OPENEXCHANGE_URL"],
            settings.CURRENCY_CONVERTER["OPENEXCHANGE_APP_ID"]
        )

        # Change the base currency whether it is specified in settings
        base_url += "&base=%s" % self.get_base_currency()

        self.url = base_url

    def get_rates(self):
        try:
            logger.debug("Connecting to url %s" % self.url)
            request = requests.get(self.url)
            return json.loads(request.content)['rates']

        except Exception as e:
            logger.exception("Error retrieving data from %s", self.url)
            raise RateBackendError("Error retrieving rates: %s" % e)

    def get_base_currency(self):
        return settings.CURRENCY_CONVERTER["OPENEXCHANGE_BASE_CURRENCY"]