from __future__ import unicode_literals

import json

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse

from ..core.utils import build_absolute_uri
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
    site = get_current_site(request)
    url = build_absolute_uri(location='/')
    data = {
        '@context': 'http://schema.org',
        '@type': 'WebSite',
        'url': url,
        'name': site.name,
        'description': site.settings.description}
    if bool(settings.SEARCH_BACKENDS):
        data['potentialAction'] = {
            '@type': 'SearchAction',
            'target': '%s%s?q={search_term}' % (url, reverse('search:search')),
            'query-input': 'required name=search_term'}
    return {'webpage_schema': json.dumps(data)}
