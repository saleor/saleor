from django.core.management import call_command
import pytest


@pytest.mark.integration
@pytest.mark.vcr(record_mode='once')
def test_index_products(product_list):
    call_command('update_index')

