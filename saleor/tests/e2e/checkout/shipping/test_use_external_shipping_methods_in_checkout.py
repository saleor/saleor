import pytest
import vcr

from ...apps.utils import add_app
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions, request_matcher
from ...webhooks.utils import create_webhook
from ..utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.vcr
@pytest.mark.e2e
def test_use_external_shipping_methods_in_checkout_core_1652(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_apps,
    settings,
    vcr_cassette_dir,
):
    # Before
    settings.PLUGINS = [
        "saleor.plugins.webhook.plugin.WebhookPlugin",
        "saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin",
    ]
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_apps,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    warehouse_id = shop_data["warehouse"]["id"]
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]

    app_input = {"name": "external_shipping", "permissions": ["MANAGE_SHIPPING"]}
    app_data = add_app(e2e_staff_api_client, app_input)
    app_id = app_data["app"]["id"]

    target_url = "http://localhost:8080"
    webhook_input = {
        "app": app_id,
        "syncEvents": ["SHIPPING_LIST_METHODS_FOR_CHECKOUT"],
        "asyncEvents": [],
        "isActive": True,
        "name": "external shipping methods",
        "targetUrl": target_url,
        "query": "subscription {\n  event {\n    ... on ShippingListMethodsForCheckout {\n      __typename\n      checkout{\n        shippingAddress{\n          country{\n            code\n          }\n        }\n      }\n    }\n  }\n}\n",
        "customHeaders": "{}",
    }
    create_webhook(e2e_staff_api_client, webhook_input)

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=9.99,
    )
    product_variant_price = float(product_variant_price)

    # Step 1 - Create checkout for product
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 4,
        },
    ]
    my_vcr = vcr.VCR()
    my_vcr.register_matcher("shipping_cassette", request_matcher)
    with my_vcr.use_cassette(
        f"{vcr_cassette_dir}/test_use_external_shipping_methods_in_checkout_core_1652.yaml",
        match_on=["shipping_cassette"],
    ):
        checkout_data = checkout_create(
            e2e_not_logged_api_client,
            lines,
            channel_slug,
            email="testEmail@example.com",
            set_default_billing_address=True,
            set_default_shipping_address=True,
        )
    checkout_id = checkout_data["id"]
    assert checkout_data["isShippingRequired"] is True
    calculated_subtotal = product_variant_price * 4
    assert checkout_data["totalPrice"]["gross"]["amount"] == calculated_subtotal
    shipping_methods = checkout_data["shippingMethods"]
    assert len(shipping_methods) == 3
    saleor_shipping = shipping_methods[0]
    assert saleor_shipping["name"] == "Test shipping method"
    assert saleor_shipping["price"]["amount"] == 10
    external_shipping_1 = shipping_methods[1]
    assert external_shipping_1["name"] == "Provider - Economy"
    assert external_shipping_1["price"]["amount"] == 100
    assert external_shipping_1["maximumDeliveryDays"] == 7
    external_shipping_2 = shipping_methods[2]
    assert external_shipping_2["name"] == "Pocztex"
    assert external_shipping_2["price"]["amount"] == 21.37
    assert external_shipping_2["maximumDeliveryDays"] == 7

    external_shipping_2_id = external_shipping_2["id"]
    shipping_price = external_shipping_2["price"]["amount"]

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        external_shipping_2_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == external_shipping_2_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    calculated_total = calculated_subtotal + shipping_price
    assert total_gross_amount == calculated_total

    # Step 3 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 4 - Complete checkout and check total
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == calculated_total
    assert order_data["deliveryMethod"]["id"] == external_shipping_2_id
    assert order_data["deliveryMethod"]["price"]["amount"] == shipping_price
    assert order_data["deliveryMethod"]["name"] == "Pocztex"
