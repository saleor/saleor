from __future__ import unicode_literals

from babel.numbers import get_territory_currencies
from django.conf import settings
from django.core.checks import register, Tags, Warning
from django_countries import countries
from django_countries.fields import Country
from geolite2 import geolite2

TOKEN_PATTERN = ('(?P<token>[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}'
                 '-[0-9a-z]{12})')


def get_country_by_ip(ip_address):
    reader = geolite2.reader()
    geo_data = reader.get(ip_address)
    geolite2.close()
    if geo_data and 'country' in geo_data and 'iso_code' in geo_data['country']:
        country_iso_code = geo_data['country']['iso_code']
        if country_iso_code in countries:
            return Country(country_iso_code)


def get_currency_for_country(country):
    currencies = get_territory_currencies(country.code)
    if len(currencies):
        main_currency = currencies[0]
        if main_currency in settings.AVAILABLE_CURRENCIES:
            return main_currency
    return settings.DEFAULT_CURRENCY


@register()
def check_session_caching(app_configs, **kwargs):
    errors = []
    cached_engines = {
        'django.contrib.sessions.backends.cache',
        'django.contrib.sessions.backends.cached_db'}
    if ('locmem' in settings.CACHES['default']['BACKEND'] and
            settings.SESSION_ENGINE in cached_engines):
        errors.append(
            Warning(
                'Session caching cannot work with locmem backend',
                'User sessions need to be globally shared, use a cache server like Redis.',
                'saleor.W001'))
    return errors
