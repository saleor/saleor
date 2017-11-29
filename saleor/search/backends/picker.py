from __future__ import unicode_literals

from django.conf import settings
from . import (elasticsearch, elasticsearch_dashboard, postgresql,
               postgresql_dashboard)


def elastic_configured():
    '''Evaluate elasticsearch configuration status'''
    return settings.ES_URL and not settings.PREFER_DB_SEARCH


def pick_backend():
    '''Get storefront search function of configured backend

    :rtype: callable with one argument of type str

    '''
    if elastic_configured():
        return elasticsearch.search
    return postgresql.search


def pick_dashboard_backend():
    '''Get dashboard search function of configured backend

    :rtype: callable with one argument of type str

    '''
    if elastic_configured():
        return elasticsearch_dashboard.search
    return postgresql_dashboard.search
