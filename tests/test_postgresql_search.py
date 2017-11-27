from __future__ import unicode_literals

from django.core.urlresolvers import reverse
import pytest


@pytest.fixture(scope='function', autouse=True)
def postgresql_search_enabled(settings):
    settings.ELASTICSEARCH_URL = None
    settings.ENABLE_SEARCH = True
    settings.PREFER_DB_SEARCH = True


@pytest.mark.integration
def test_dummy_integration(client):
    phrase = 'foo'
    client.get(reverse('search:search'), {'q': phrase})


@pytest.mark.integration
def test_dummy_dashboard_integration(client):
    phrase = 'foo'
    client.get(reverse('dashboard:search'), {'q': phrase})
