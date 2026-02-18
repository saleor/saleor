import json
from decimal import Decimal

import graphene
from measurement.measures import Weight
from prices import Money

from .....shipping.interface import ShippingMethodData
from ....webhooks.exclude_shipping import (
    _generate_excluded_shipping_methods_for_checkout_payload,
)


def test_generate_excluded_shipping_methods_for_checkout(checkout):
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )
    response = json.loads(
        _generate_excluded_shipping_methods_for_checkout_payload(
            checkout, [shipping_method]
        )
    )

    assert "checkout" in response
    assert response["shipping_methods"] == [
        {
            "id": graphene.Node.to_global_id("ShippingMethod", "123"),
            "price": "10.59",
            "currency": "USD",
            "name": "shipping",
            "maximum_order_weight": "10.0:kg",
            "minimum_order_weight": "1.0:g",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]


def test_generate_excluded_shipping_methods_for_checkout_payload(
    checkout_with_items,
):
    # given
    shipping_method = ShippingMethodData(
        id="123",
        price=Money(Decimal("10.59"), "USD"),
        name="shipping",
        maximum_order_weight=Weight(kg=10),
        minimum_order_weight=Weight(g=1),
        maximum_delivery_days=10,
        minimum_delivery_days=2,
    )

    # when
    json_payload = json.loads(
        _generate_excluded_shipping_methods_for_checkout_payload(
            checkout_with_items, available_shipping_methods=[shipping_method]
        )
    )
    # then
    assert len(json_payload["shipping_methods"]) == 1
    assert json_payload["shipping_methods"][0]["id"] == graphene.Node.to_global_id(
        "ShippingMethod", shipping_method.id
    )

    assert "checkout" in json_payload
    assert "channel" in json_payload["checkout"]
