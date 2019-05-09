import re
from decimal import Decimal, InvalidOperation

from babel.core import Locale, UnknownLocaleError, get_global
from babel.numbers import format_currency
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, to_locale

from django_babel.templatetags.babel import currencyfmt

register = template.Library()


def get_currency_fraction(currency):
    fractions = get_global('currency_fractions')
    try:
        fraction = fractions[currency]
    except KeyError:
        fraction = fractions['DEFAULT']
    return fraction[0]


def format_price(value, currency, html=False):
    """
    Format decimal value as currency
    """
    try:
        value = Decimal(value)
    except (TypeError, InvalidOperation):
        return ''

    locale, locale_code = get_locale_data()
    pattern = locale.currency_formats.get('standard').pattern

    if html:
        pattern = re.sub(
            '(\xa4+)', '<span class="currency">\\1</span>', pattern)

    result = format_currency(
        value, currency, format=pattern, locale=locale_code)
    return mark_safe(result)


def get_locale_data():
    language = get_language()
    if not language:
        language = settings.LANGUAGE_CODE
    locale_code = to_locale(language)
    locale = None
    try:
        locale = Locale.parse(locale_code)
    except (ValueError, UnknownLocaleError):
        # Invalid format or unknown locale
        # Fallback to the default language
        language = settings.LANGUAGE_CODE
        locale_code = to_locale(language)
        locale = Locale.parse(locale_code)
    return locale, locale_code


@register.filter
def amount(obj, format='text'):
    if format == 'text':
        return format_price(
            obj.amount, obj.currency, html=False)
    if format == 'html':
        return format_price(
            obj.amount, obj.currency, html=True)
    return currencyfmt(obj.amount, obj.currency)
