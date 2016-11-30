from django import template
from ..utils import get_pricing_info

register = template.Library()


@register.assignment_tag
def pricing_info_for_product(product, discounts=None, local_currency=None):
    return get_pricing_info(product, discounts, local_currency)
