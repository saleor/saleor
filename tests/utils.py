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


def get_form_errors(response, form_name='form'):
    errors = response.context.get(form_name).errors
    return errors.get('__all__') if errors else []
