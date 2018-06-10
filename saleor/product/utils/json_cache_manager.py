import json

from celery import shared_task
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder

from ..models import Product, PRODUCT_LIST_CACHE_KEY


def _get_product_list_as_dict():
    products = Product.objects.prefetch_related(
        'images', 'variants',
        'category',
        'product_type__product_attributes__values',
        'product_type__variant_attributes__values').all()
    results = [product.as_dict() for product in products]
    return results


def _get_product_list_as_json():
    return json.dumps(
        {'products': _get_product_list_as_dict()}, cls=DjangoJSONEncoder)


def cached_product_list_as_json():
    return cache.get_or_set(PRODUCT_LIST_CACHE_KEY, _get_product_list_as_json)


@shared_task
def refresh_json_product_list_cache():
    cache.set(PRODUCT_LIST_CACHE_KEY, _get_product_list_as_json())
