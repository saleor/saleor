from __future__ import unicode_literals

from django.conf import settings
from . import (elasticsearch, elasticsearch_dashboard, postgresql,
               postgresql_dashboard)


def elastic_configured():
    return settings.ES_URL and not settings.PREFER_DB_SEARCH


def pick_backend():
    if elastic_configured():
        return elasticsearch.search
    return postgresql.search


def pick_dashboard_backend():
    if elastic_configured():
        return elasticsearch_dashboard.search
    return postgresql_dashboard.search
