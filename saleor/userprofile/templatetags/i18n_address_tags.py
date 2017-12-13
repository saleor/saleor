from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext
import i18naddress

from ...userprofile.models import Address

register = template.Library()


@register.simple_tag
def format_address(address, latin=False):
    address_data = Address.objects.as_data(address)
    address_data['name'] = pgettext(
        'Address data', '%(first_name)s %(last_name)s') % address_data
    address_data['country_code'] = address_data['country']
    address_data['street_address'] = pgettext(
        'Address data',
        '%(street_address_1)s\n'
        '%(street_address_2)s' % address_data)
    formatted_address = i18naddress.format_address(address_data, latin)
    return mark_safe(formatted_address)
