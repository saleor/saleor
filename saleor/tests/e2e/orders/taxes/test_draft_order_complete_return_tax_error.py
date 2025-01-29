import pytest

from ... import DEFAULT_ADDRESS
from ...apps.utils import add_app
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_default_shop
from ...taxes.utils import get_tax_configurations, update_tax_configuration
from ...utils import assign_permissions
from ...webhooks.utils import create_webhook
from ..utils import (
    draft_order_create,
    draft_order_update,
    order_lines_create,
    raw_draft_order_complete,
)


@pytest.mark.e2e
def test_draft_order_complte_return_tax_error_when_app_not_respond_CORE_2015(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_apps,
    permission_handle_taxes,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_apps,
        permission_handle_taxes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]
    shipping_price = 10

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

    (_product_id, product_variant_id, product_variant_price) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=200,
    )
    product_variant_price = float(product_variant_price)

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "userEmail": "test_user@test.com",
        "shippingAddress": DEFAULT_ADDRESS,
        "billingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input,
    )
    order_id = data["order"]["id"]

    # Step 2 - Add lines to the order
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_data = order_data["order"]
    assert order_data["total"]["gross"]["amount"] == product_variant_price
    assert order_data["total"]["net"]["amount"] == product_variant_price
    # Tax is not calculated, app do not respond
    assert order_data["total"]["tax"]["amount"] == 0

    # Step 3 - Add a shipping method
    input = {"shippingMethod": shipping_method_id}
    order_data = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_data = order_data["order"]
    assert order_data["shippingPrice"]["gross"]["amount"] == shipping_price
    assert order_data["shippingPrice"]["net"]["amount"] == shipping_price
    # Tax is not calculated, app do not respond
    assert order_data["shippingPrice"]["tax"]["amount"] == 0
    calculated_total_net = product_variant_price + shipping_price
    assert order_data["total"]["net"]["amount"] == calculated_total_net
    assert order_data["total"]["gross"]["amount"] == calculated_total_net
    # Tax is not calculated, app do not respond
    assert order_data["total"]["tax"]["amount"] == 0

    # Step 4 - Complete the draft order
    order = raw_draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["errors"] is not None
    assert order["errors"][0]["code"] == "TAX_ERROR"
    assert (
        order["errors"][0]["message"] == "Configured Tax App returned invalid response."
    )
