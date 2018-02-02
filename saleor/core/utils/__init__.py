import decimal
from json import JSONEncoder
from urllib.parse import urljoin

from babel.numbers import get_territory_currencies
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.utils.encoding import iri_to_uri, smart_text
from django_countries import countries
from django_countries.fields import Country
from django_prices_openexchangerates import exchange_currency
from geolite2 import geolite2
from prices import PriceRange

from ...userprofile.models import User

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


def to_local_currency(price, currency):
    if not settings.OPENEXCHANGERATES_API_KEY:
        return None
    if isinstance(price, PriceRange):
        from_currency = price.min_price.currency
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
