from __future__ import unicode_literals

from babel.numbers import get_territory_currencies
from django.conf import settings
from django_countries import countries
from django_countries.fields import Country
from geoip import geolite2

TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')


def get_country_by_ip(ip_address):
    geo_data = geolite2.lookup(ip_address)
    if geo_data and geo_data.country in countries:
        return Country(geo_data.country)


def get_currency_for_country(country):
    currencies = get_territory_currencies(country.code)
    if len(currencies):
        main_currency = currencies[0]
        if main_currency in settings.AVAILABLE_CURRENCIES:
            return main_currency
    return settings.DEFAULT_CURRENCY
