from django import template
import i18naddress
from django.utils.safestring import mark_safe
from ...userprofile.models import Address

register = template.Library()


@register.simple_tag
def format_address(address, latin=False):
    address_data = Address.objects.as_data(address)
    address_data['country_code'] = address_data['country']
    address_data['street_address'] = '%s\n%s' % (
        address_data['street_address_1'], address_data['street_address_2'])
    return mark_safe(i18naddress.format_address(address_data, latin))
