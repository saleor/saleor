import decimal
import logging
from json import JSONEncoder
from urllib.parse import urljoin

from babel.numbers import get_territory_currencies
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.encoding import iri_to_uri, smart_text
from django_babel.templatetags.babel import currencyfmt
from django_countries import countries
from django_countries.fields import Country
from django_prices_openexchangerates import exchange_currency
from django_prices_vatlayer.utils import (
    get_tax_rates_for_country, get_tax_for_rate)
from geolite2 import geolite2
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange
from versatileimagefield.image_warmer import VersatileImageFieldWarmer

from ...account.models import User

ZERO_TAXED_MONEY = TaxedMoney(
    net=Money(0, settings.DEFAULT_CURRENCY),
    gross=Money(0, settings.DEFAULT_CURRENCY))

DEFAULT_TAX_RATE_NAME = 'standard'

georeader = geolite2.reader()
logger = logging.getLogger(__name__)


class CategoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # pylint: disable=W0212
        level = getattr(obj, obj._mptt_meta.level_attr)
        indent = max(0, level - 1) * '│'
        if obj.parent:
            last = ((obj.parent.rght - obj.rght == 1) and
                    (obj.rght - obj.lft == 1))
            if last:
                indent += '└ '
            else:
                indent += '├ '
        return '%s%s' % (indent, smart_text(obj))


def build_absolute_uri(location):
    # type: (str, bool, saleor.site.models.SiteSettings) -> str
    host = Site.objects.get_current().domain
    protocol = 'https' if settings.ENABLE_SSL else 'http'
    current_uri = '%s://%s' % (protocol, host)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if ip:
        return ip.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', None)


def get_country_by_ip(ip_address):
    geo_data = georeader.get(ip_address)
    if (
            geo_data and
            'country' in geo_data and
            'iso_code' in geo_data['country']):
        country_iso_code = geo_data['country']['iso_code']
        if country_iso_code in countries:
            return Country(country_iso_code)
    return None


def get_currency_for_country(country):
    currencies = get_territory_currencies(country.code)
    if currencies:
        return currencies[0]
    return settings.DEFAULT_CURRENCY


def get_paginator_items(items, paginate_by, page_number):
    if not page_number:
        page_number = 1
    paginator = Paginator(items, paginate_by)
    try:
        page_number = int(page_number)
    except ValueError:
        raise Http404('Page can not be converted to an int.')

    try:
        items = paginator.page(page_number)
    except InvalidPage as err:
        raise Http404('Invalid page (%(page_number)s): %(message)s' % {
            'page_number': page_number, 'message': str(err)})
    return items


def format_money(money):
    return currencyfmt(money.amount, money.currency)


def get_taxes_for_country(country):
    tax_rates = get_tax_rates_for_country(country.code)
    if tax_rates is None:
        return None

    taxes = {DEFAULT_TAX_RATE_NAME: {
        'value': tax_rates['standard_rate'],
        'tax': get_tax_for_rate(tax_rates)}}
    if tax_rates['reduced_rates']:
        taxes.update({
            rate_name: {
                'value': tax_rates['reduced_rates'][rate_name],
                'tax': get_tax_for_rate(tax_rates, rate_name)}
            for rate_name in tax_rates['reduced_rates']})
    return taxes


def apply_tax_to_price(taxes, rate_name, base):
    if not taxes or not rate_name:
        # Naively convert Money to TaxedMoney for consistency with price
        # handling logic across the codebase, passthrough other money types
        if isinstance(base, Money):
            return TaxedMoney(net=base, gross=base)
        if isinstance(base, MoneyRange):
            return TaxedMoneyRange(
                apply_tax_to_price(taxes, rate_name, base.start),
                apply_tax_to_price(taxes, rate_name, base.stop))
        if isinstance(base, (TaxedMoney, TaxedMoneyRange)):
            return base
        raise TypeError('Unknown base for flat_tax: %r' % (base,))

    if rate_name in taxes:
        tax_to_apply = taxes[rate_name]['tax']
    else:
        tax_to_apply = taxes[DEFAULT_TAX_RATE_NAME]['tax']

    keep_gross = Site.objects.get_current().settings.include_taxes_in_prices
    return tax_to_apply(base, keep_gross=keep_gross)


def to_local_currency(price, currency):
    if not settings.OPENEXCHANGERATES_API_KEY:
        return None
    if isinstance(price, MoneyRange):
        from_currency = price.start.currency
    else:
        from_currency = price.currency
    if currency != from_currency:
        try:
            return exchange_currency(price, currency)
        except ValueError:
            pass
    return None


def get_user_shipping_country(request):
    if request.user.is_authenticated:
        default_shipping = request.user.default_shipping_address
        if default_shipping:
            return default_shipping.country
    return request.country


def serialize_decimal(obj):
    if isinstance(obj, decimal.Decimal):
        return str(obj)
    return JSONEncoder().default(obj)


def create_superuser(credentials):
    user, created = User.objects.get_or_create(
        email=credentials['email'], defaults={
            'is_active': True, 'is_staff': True, 'is_superuser': True})
    if created:
        user.set_password(credentials['password'])
        user.save()
        msg = 'Superuser - %(email)s/%(password)s' % credentials
    else:
        msg = 'Superuser already exists - %(email)s' % credentials
    return msg


def create_thumbnails(pk, model, size_set, image_attr=None):
    instance = model.objects.get(pk=pk)
    if not image_attr:
        image_attr = 'image'
    image_instance = getattr(instance, image_attr)
    if image_instance.name == '':
        # There is no file, skip processing
        return
    warmer = VersatileImageFieldWarmer(
        instance_or_queryset=instance,
        rendition_key_set=size_set, image_attr=image_attr)
    logger.info('Creating thumbnails for  %s', pk)
    num_created, failed_to_create = warmer.warm()
    if num_created:
        logger.info('Created %d thumbnails', num_created)
    if failed_to_create:
        logger.error('Failed to generate thumbnails',
                     extra={'paths': failed_to_create})
