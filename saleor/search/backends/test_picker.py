from __future__ import unicode_literals

from .picker import pick_backend
from . import postgresql, elasticsearch


def test_picks_db(settings):
    settings.ELASTICSEARCH_URL = None
    assert pick_backend() is postgresql.search


def test_pick_elastic_when_configured(settings):
    settings.ELASTICSEARCH_URL = 'whatever'
    settings.PREFER_DB_SEARCH = False
    assert pick_backend() is elasticsearch.search


def test_pick_db_when_preferred(settings):
    settings.ELASTICSEARCH = 'whatever'
    settings.PREFER_DB_SEARCH = True
    assert pick_backend() is postgresql.search
