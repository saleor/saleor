import json

from django.conf import settings
from django.db.models import Q
from django.urls import translate_url
from django.utils.encoding import smart_text


def get_redirect_location(response):
    path = response['Location']
    return translate_url(path, lang_code=settings.LANGUAGE_CODE)


def filter_products_by_attribute(queryset, attribute_id, value):
    key = smart_text(attribute_id)
    value = smart_text(value)
    in_product = Q(attributes__contains={key: value})
    in_variant = Q(variants__attributes__contains={key: value})
    return queryset.filter(in_product | in_variant)


def get_graphql_content(response):
    return json.loads(response.content.decode('utf8'))
