from django import template

from ..models import OrderLine

register = template.Library()


@register.simple_tag()
def display_translated_order_line_name(order_line: OrderLine):
    product_name = order_line.translated_product_name or order_line.product_name
    variant_name = order_line.translated_variant_name or order_line.variant_name
    return f"{product_name} ({variant_name})" if variant_name else product_name
