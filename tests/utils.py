try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from django.db.models import Q
from django.utils.encoding import smart_text


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    location = response['Location']
    if location.startswith('http'):
        url = urlparse(location)
        location = url.path
    return location


def filter_products_by_attribute(queryset, attribute_id, value):
    key = smart_text(attribute_id)
    value = smart_text(value)
    in_product = Q(attributes__contains={key: value})
    in_variant = Q(variants__attributes__contains={key: value})
    return queryset.filter(in_product | in_variant)
