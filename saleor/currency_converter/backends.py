from __future__ import unicode_literals

import json

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from purl import URL
import requests

from .models import OpenExchangeRate


class OpenExchangeBackend(object):
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
        request = requests.get(self.url)
        return json.loads(request.content)['rates']

    def get_base_currency(self):
        return settings.OPENEXCHANGE["BASE_CURRENCY"]

    def update_rates(self):
        """
        Creates or updates rates from OpenExchange
        """

        for currency, exchange_rate in self.get_rates().items():
            OpenExchangeRate.objects.get_or_create(
                source_currency=self.get_base_currency(),
                target_currency=currency,
                exchange_rate=exchange_rate)