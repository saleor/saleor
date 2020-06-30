import pytest
from django.core.exceptions import ValidationError

from ..utils.product_variants import product_variant_exist, products_variant_exist


def test_product_variant_exist(product):
    assert product_variant_exist(product) is None

    product.variants.all().delete()

    with pytest.raises(ValidationError):
        product_variant_exist(product)


def test_products_variant_exist(product_list):
    assert products_variant_exist(product_list) is None

    product_list[0].variants.first().delete()

    with pytest.raises(ValidationError):
        products_variant_exist(product_list)
