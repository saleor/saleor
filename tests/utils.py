import json
from urllib.parse import urlparse

from django.db.models import Q
from django.utils.encoding import smart_text


def get_url_path(url):
    parsed_url = urlparse(url)
    return parsed_url.path


def get_redirect_location(response):
    # Due to Django 1.8 compatibility, we have to handle both cases
    return get_url_path(response['Location'])


def filter_products_by_attribute(queryset, attribute_id, value):
    key = smart_text(attribute_id)
    value = smart_text(value)
    in_product = Q(attributes__contains={key: value})
    in_variant = Q(variants__attributes__contains={key: value})
    return queryset.filter(in_product | in_variant)


def get_graphql_content(response):
    return json.loads(response.content.decode('utf8'))


def seo_field_test_helper(object, function_name, field_values, expected_result):
    """Helper for testing seo fields."""
    for field_name, field_value in field_values.items():
        setattr(object, field_name, field_value)
    object.save()
    get_seo_field_function = getattr(object, function_name)
    result = get_seo_field_function()
    assert expected_result == result
