from __future__ import unicode_literals

import json

from django.template import Library

from saleor.product.utils import product_json_ld

register = Library()


@register.simple_tag
def product_availability_schema(product):
    return json.dumps(product_json_ld(product))
