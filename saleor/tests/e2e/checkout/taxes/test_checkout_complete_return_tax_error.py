import pytest

from ...apps.utils import add_app
from ...product.utils.preparing_product import prepare_product
from ...shop.utils import prepare_default_shop
from ...taxes.utils import get_tax_configurations, update_tax_configuration
from ...utils import assign_permissions
from ...webhooks.utils import create_webhook
from ..utils import (
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    raw_checkout_complete,
)


@pytest.mark.e2e
def test_checkout_calculate_return_tax_error_when_app_not_respond_CORE_2013(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_apps,
    permission_handle_taxes,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_apps,
        permission_handle_taxes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    app_input = {"name": "tax_app", "permissions": ["HANDLE_TAXES"]}
    app_data = add_app(e2e_staff_api_client, app_input)
    app_id = app_data["app"]["id"]

    target_url = "http://localhost:8777"
    webhook_input = {
        "app": app_id,
        "syncEvents": ["CHECKOUT_CALCULATE_TAXES"],
        "asyncEvents": [],
        "isActive": True,
        "name": "dynamic taxes",
        "targetUrl": target_url,
        "query": "fragment TaxBaseLine on TaxableObjectLine {\n  sourceLine {\n    __typename\n    ... on CheckoutLine {\n      id\n      checkoutVariant: variant {\n        id\n        product {\n          taxClass {\n            id\n            name\n          }\n        }\n      }\n    }\n    ... on OrderLine {\n      id\n      orderVariant: variant {\n        id\n        product {\n          taxClass {\n            id\n            name\n          }\n        }\n      }\n    }\n  }\n  quantity\n  unitPrice {\n    amount\n  }\n  totalPrice {\n    amount\n  }\n  chargeTaxes\n}\n\nfragment TaxBase on TaxableObject {\n  pricesEnteredWithTax\n  currency\n  channel {\n    slug\n  }\n  shippingPrice {\n    amount\n  }\n  lines {\n    ...TaxBaseLine\n  }\n  discounts {\n    name\n    amount {\n      amount\n      currency\n    }\n  }\n  sourceObject {\n    __typename\n    ... on Checkout {\n      id\n    }\n    ... on Order {\n      id\n    }\n  }\n}\n\nfragment CalculateTaxesEvent on Event {\n  ... on CalculateTaxes {\n    taxBase {\n      ...TaxBase\n    }\n  }\n}\n\nsubscription CalculateTaxes {\n  event {\n    ...CalculateTaxesEvent\n  }\n}\n",
        "customHeaders": "{}",
    }
    create_webhook(e2e_staff_api_client, webhook_input)

    tax_configs = get_tax_configurations(e2e_staff_api_client)
    assert len(tax_configs) == 1
    tax_config_id = tax_configs[0]["node"]["id"]

    update_tax_configuration(
        e2e_staff_api_client,
        tax_config_id,
        tax_calculation_strategy="TAX_APP",
        display_gross_prices=True,
        prices_entered_with_tax=False,
        tax_app_id=app_id,
    )

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=30,
    )
    product_variant_price = float(product_variant_price)

    # Step 1 - Create checkout
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
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["totalPrice"]["gross"]["amount"] == product_variant_price
    assert checkout_data["totalPrice"]["net"]["amount"] == product_variant_price
    # Tax is not calculated, app do not respond
    assert checkout_data["totalPrice"]["tax"]["amount"] == 0

    # Step 2 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    shipping_price = 10
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingPrice"]["gross"]["amount"] == shipping_price
    assert checkout_data["shippingPrice"]["net"]["amount"] == shipping_price
    # Tax is not calculated, app do not respond
    assert checkout_data["shippingPrice"]["tax"]["amount"] == 0
    calculated_total_net = product_variant_price + shipping_price
    assert checkout_data["totalPrice"]["net"]["amount"] == calculated_total_net

    # Step 3 - Create payment for checkout
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        calculated_total_net,
    )

    # Step 4 - Complete checkout
    order_data = raw_checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["errors"] is not None
    assert order_data["errors"][0]["code"] == "TAX_ERROR"
    assert (
        order_data["errors"][0]["message"]
        == "Configured Tax App returned invalid response."
    )
