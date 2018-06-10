from unittest import mock

from django.core.cache import cache

from saleor.product.utils.json_cache_manager import (
    cached_product_list_as_json,
    refresh_json_product_list_cache)


@mock.patch.object(cache, 'add')
def test_get_non_and_cached_json_list(mocked_cached_add, product):
    cached_product_list_as_json()
    cached_product_list_as_json()
    assert mocked_cached_add.called_once


def test_refresh_json_product_list_cache(product):
    product.name = '...hello world.'
    product.save()

    assert product.name in cached_product_list_as_json()

    product.name = '...goodbye world.'
    product.save()

    assert product.name not in cached_product_list_as_json()

    refresh_json_product_list_cache()
    assert product.name in cached_product_list_as_json()
