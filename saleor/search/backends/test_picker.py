from __future__ import unicode_literals

from .picker import pick_backend, pick_dashboard_backend
from . import (postgresql, postgresql_dashboard, elasticsearch_dashboard,
               elasticsearch)


POSTGRES_STOREFRONT_BACKEND = postgresql.search
POSTGRES_DASHBOARD_BACKEND = postgresql_dashboard.search
ELASTIC_STOREFRONT_BACKEND = elasticsearch.search
ELASTIC_DASHBOARD_BACKEND = elasticsearch_dashboard.search


def test_picks_db(settings):
    settings.ELASTICSEARCH_URL = None
    assert pick_backend() is POSTGRES_STOREFRONT_BACKEND
    assert pick_dashboard_backend() is POSTGRES_DASHBOARD_BACKEND


def test_pick_elastic_when_configured(settings):
    settings.ELASTICSEARCH_URL = 'whatever'
    settings.PREFER_DB_SEARCH = False
    assert pick_backend() is ELASTIC_STOREFRONT_BACKEND
    assert pick_dashboard_backend() is ELASTIC_DASHBOARD_BACKEND


def test_pick_db_when_preferred(settings):
    settings.ELASTICSEARCH = 'whatever'
    settings.PREFER_DB_SEARCH = True
    assert pick_backend() is POSTGRES_STOREFRONT_BACKEND
    assert pick_dashboard_backend() is POSTGRES_DASHBOARD_BACKEND
