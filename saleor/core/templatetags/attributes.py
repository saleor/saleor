from django.template import Library

from ...product.utils import get_attributes_display_map

register = Library()

ATTRIBUTE_EMPTY_VALUE = '-'


@register.filter
def attributes_values_with_empty(variant, attributes):
    attr_values = get_attributes_display_map(variant, attributes)
    values = []
    for attribute in attributes:
        if attribute.pk in attr_values:
            values.append(attr_values[attribute.pk])
        else:
            values.append(ATTRIBUTE_EMPTY_VALUE)
    return values
