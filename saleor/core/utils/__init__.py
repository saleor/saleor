# coding: utf-8
from __future__ import unicode_literals

from babel.numbers import get_territory_currencies
from django import forms
from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.encoding import iri_to_uri, smart_text
from django_countries import countries
from django_countries.fields import Country
from django_prices_openexchangerates import exchange_currency
from geolite2 import geolite2
from prices import PriceRange

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

georeader = geolite2.reader()


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


def build_absolute_uri(location, is_secure=False):
    from django.contrib.sites.models import Site
    site = Site.objects.get_current()
    host = site.domain
    current_uri = '%s://%s' % ('https' if is_secure else 'http', host)
    location = urljoin(current_uri, location)
    return iri_to_uri(location)


def get_client_ip(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', None)
    if ip:
        return ip.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', None)


def get_country_by_ip(ip_address):
    geo_data = georeader.get(ip_address)
    if geo_data and 'country' in geo_data and 'iso_code' in geo_data['country']:
        country_iso_code = geo_data['country']['iso_code']
        if country_iso_code in countries:
            return Country(country_iso_code)


def get_currency_for_country(country):
    currencies = get_territory_currencies(country.code)
    if len(currencies):
        return currencies[0]
    return settings.DEFAULT_CURRENCY


def get_paginator_items(items, paginate_by, page):
    paginator = Paginator(items, paginate_by)
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)
    return items


def to_local_currency(price, currency):
    if not settings.OPENEXCHANGERATES_API_KEY:
        return
    if isinstance(price, PriceRange):
        from_currency = price.min_price.currency
    else:
        from_currency = price.currency
    if currency != from_currency:
        try:
            return exchange_currency(price, currency)
        except ValueError:
            pass
