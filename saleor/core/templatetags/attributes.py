from django.template import Library
from saleor.product.utils import get_attributes_display

register = Library()

ATTRIBUTE_EMPTY_VALUE = '-'


@register.filter
def get_attributes_values(variant, attributes):
    attr_values = get_attributes_display(variant, attributes)
    values = []
    for attribute in attributes:
        if attribute.pk in attr_values:
            values.append(attr_values[attribute.pk])
        else:
            values.append(ATTRIBUTE_EMPTY_VALUE)
    return values
