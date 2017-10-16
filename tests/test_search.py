from django.core.management import call_command
from django.core.urlresolvers import reverse
import pytest


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once')
def test_index_products(product_list):
    options = {'backend_name': 'default'}
    call_command('update_index', **options)


@pytest.mark.integration
@pytest.mark.vcr(
    record_mode='once', match_on=['url', 'method', 'body'])
def test_search_with_empty_result(db, client):
    WORD = 'foo'
    client.get(reverse('search:search'), {'q': WORD})
