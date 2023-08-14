import pytest

from ..orders.utils.draft_order import draft_order_create
from ..orders.utils.order_lines import order_lines_create
from .utils import checkout_create_from_order


def prepare_order(e2e_superuser_api_client, prepare_product):
    product_variant_id, channel_id = prepare_product
    data = draft_order_create(
        e2e_superuser_api_client,
        channel_id,
    )

    order_id = data["order"]["id"]
    order_lines = [{"variantId": product_variant_id, "quantity": 1, "price": 100}]
    order_data = order_lines_create(e2e_superuser_api_client, order_id, order_lines)
    order_product_variant_id = order_data["order"]["lines"][0]["variant"]
    order_product_quantity = order_data["order"]["lines"][0]["quantity"]

    return (
        order_id,
        order_product_variant_id,
        order_product_quantity,
    )


@pytest.mark.e2e
def test_checkout_create_from_order_core_0104(
    e2e_superuser_api_client, prepare_product
):
    # Before
    order_id, order_product_variant_id, order_product_quantity = prepare_order(
        e2e_superuser_api_client, prepare_product
    )

    # Step 1 - Create checkout from order

    checkout_data = checkout_create_from_order(e2e_superuser_api_client, order_id)
    checkout_id = checkout_data["checkout"]["id"]
    assert checkout_id is not None
    errors = checkout_data["errors"]
    assert errors == []
    checkout_lines = checkout_data["checkout"]["lines"]
    assert checkout_lines != []

    checkout_product_variant_id = checkout_lines[0]["variant"]["id"]
    checkout_product_quantity = checkout_lines[0]["quantity"]
    order_product_variant_id_value = order_product_variant_id["id"]

    assert checkout_product_variant_id == order_product_variant_id_value
    assert checkout_product_quantity == order_product_quantity
