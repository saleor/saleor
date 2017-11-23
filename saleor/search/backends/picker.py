from __future__ import unicode_literals

from django.conf import settings
from . import elasticsearch, postgresql


def pick_backend():
    if settings.ELASTICSEARCH_URL and not settings.PREFER_DB_SEARCH:
        return elasticsearch.search
    return postgresql.search
