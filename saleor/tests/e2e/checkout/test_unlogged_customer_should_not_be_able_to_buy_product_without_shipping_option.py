import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import checkout_create, raw_checkout_dummy_payment_create


@pytest.mark.e2e
def test_unlogged_customer_unable_to_buy_product_without_shipping_option_CORE_0106(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [],
                    },
                ],
                "order_settings": {},
            }
        ],
        shop_settings={},
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]

    variant_price = 10

    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Step 1 - Create checkout with no shipping method
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
    )
    checkout_id = checkout_data["id"]
    checkout_shipping_required = checkout_data["isShippingRequired"]
    shipping_methods = checkout_data["shippingMethods"]

    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert checkout_shipping_required is True
    assert shipping_methods == []
    assert checkout_data["availableCollectionPoints"] == []

    # Step 2 - Create dummy payment and verify no purchase was made
    checkout_payment_data = raw_checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
        token="fully_charged",
    )
    errors = checkout_payment_data["errors"]

    assert errors[0]["code"] == "SHIPPING_METHOD_NOT_SET"
    assert errors[0]["field"] == "shippingMethod"
    assert errors[0]["message"] == "Shipping method is not set"
