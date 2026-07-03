import json
from unittest.mock import ANY

import graphene

from .... import __version__
from ...webhooks.payloads import (
    generate_product_variant_with_stock_payload,
)


def test_generate_base_product_variant_payload(product_with_two_variants):
    stocks_to_serialize = [
        variant.stocks.first() for variant in product_with_two_variants.variants.all()
    ]
    first_stock, second_stock = stocks_to_serialize
    payload = json.loads(
        generate_product_variant_with_stock_payload(stocks_to_serialize)
    )
    expected_payload = [
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", first_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", first_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", first_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", first_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
        {
            "type": "Stock",
            "id": graphene.Node.to_global_id("Stock", second_stock.id),
            "product_id": graphene.Node.to_global_id(
                "Product", second_stock.product_variant.product_id
            ),
            "product_variant_id": graphene.Node.to_global_id(
                "ProductVariant", second_stock.product_variant_id
            ),
            "warehouse_id": graphene.Node.to_global_id(
                "Warehouse", second_stock.warehouse_id
            ),
            "product_slug": "test-product-with-two-variant",
            "meta": {
                "issuing_principal": {"id": None, "type": None},
                "issued_at": ANY,
                "version": __version__,
            },
        },
    ]
    assert payload == expected_payload
