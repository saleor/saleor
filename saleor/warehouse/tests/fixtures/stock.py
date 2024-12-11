import pytest

from ...models import Stock


@pytest.fixture
def stock(variant, warehouse):
    return Stock.objects.create(
        product_variant=variant, warehouse=warehouse, quantity=15
    )


@pytest.fixture
def stocks_for_cc(warehouses_for_cc, product_variant_list, product_with_two_variants):
    return Stock.objects.bulk_create(
        [
            Stock(
                warehouse=warehouses_for_cc[0],
                product_variant=product_variant_list[0],
                quantity=5,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[1],
                quantity=10,
            ),
            Stock(
                warehouse=warehouses_for_cc[1],
                product_variant=product_variant_list[2],
                quantity=10,
            ),
            Stock(
                warehouse=warehouses_for_cc[2],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[0],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[1],
                quantity=3,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_with_two_variants.variants.last(),
                quantity=7,
            ),
            Stock(
                warehouse=warehouses_for_cc[3],
                product_variant=product_variant_list[2],
                quantity=3,
            ),
        ]
    )
