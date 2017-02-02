from __future__ import unicode_literals

import json

from django.conf import settings
from django.urls import reverse

from ..product.models import Category


def get_setting_as_dict(name, short_name=None):
    short_name = short_name or name
    try:
        return {short_name: getattr(settings, name)}
    except AttributeError:
        return {}


# request is a required parameter
# pylint: disable=W0613
def default_currency(request):
    return get_setting_as_dict('DEFAULT_CURRENCY')


# request is a required parameter
# pylint: disable=W0613
def categories(request):
    return {'categories': Category.tree.root_nodes().filter(hidden=False)}


def search_enabled(request):
    return {'SEARCH_IS_ENABLED': bool(settings.SEARCH_BACKENDS)}


def webpage_schema(request):
    # Todo: add editing this data in dashboard
    data = {
        '@context': 'http://schema.org',
        '@type': 'WebSite',
        'url': settings.SITE_ADDRESS,
        'name': settings.SITE_NAME,
        'description': settings.SITE_DESCRIPTION,
    }
    if bool(settings.SEARCH_BACKENDS):
        data['potentialAction'] = {
            '@type': 'SearchAction',
            'target': '%s%s?q={search_term}' % (settings.SITE_ADDRESS,
                                                reverse('search:search')),
            'query-input': 'required name=search_term'}
    return {'webpage_schema': json.dumps(data)}
