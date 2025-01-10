import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...taxes.utils import update_country_tax_rates
from ...utils import assign_permissions
from ...vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
)
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
    order_update_shipping,
)
from ..utils.order_line_discount_update import order_line_discount_update


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
    products,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "singleUse": True,
        "applyOncePerOrder": False,
        "products": products,
    }

    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_code, voucher_discount_value


@pytest.mark.e2e
def test_draft_order_with_voucher_specific_product_and_manual_line_discount_CORE_0250(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    """Manual line discount should override line-level voucher."""
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shipping_price_net = 15
    product1_price = 30
    product2_price = 55

    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": False,
    }

    # Create channel, warehouse, shipping method and update tax configuration
    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                                "add_channels": {
                                    "price": shipping_price_net,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "automaticallyConfirmAllNewOrders": True,
                    "allowUnpaidOrders": False,
                    "includeDraftOrderInVoucherUsage": False,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]

    country_tax_rate = 10
    tax_rate = 1 + country_tax_rate / 100
    country = "US"

    update_country_tax_rates(
        e2e_staff_api_client,
        country,
        [{"rate": country_tax_rate}],
    )
    (
        product1_id,
        product1_variant_id,
        product1_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product1_price,
        product_type_slug="shoes",
    )
    (
        product2_id,
        product2_variant_id,
        product2_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product2_price,
        product_type_slug="hoodies",
    )

    # Prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Create voucher for specific product
    voucher_discount_amount = 10
    voucher_code, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="10usd_off",
        voucher_discount_type="FIXED",
        voucher_discount_value=voucher_discount_amount,
        voucher_type="SPECIFIC_PRODUCT",
        products=[product1_id, product2_id],
    )

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product1_variant_id, "quantity": 1},
        {"variantId": product2_variant_id, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_line1 = order["order"]["lines"][0]
    order_line2 = order["order"]["lines"][1]

    assert order_line1["variant"]["id"] == product1_variant_id
    assert order_line1["unitPrice"]["net"]["amount"] == product1_variant_price
    assert order_line2["variant"]["id"] == product2_variant_id
    assert order_line2["unitPrice"]["net"]["amount"] == product2_variant_price

    undiscounted_subtotal_net = round(
        product1_variant_price + product2_variant_price, 2
    )
    undiscounted_subtotal_gross = round(undiscounted_subtotal_net * tax_rate, 2)
    assert order["order"]["subtotal"]["net"]["amount"] == undiscounted_subtotal_net
    assert order["order"]["subtotal"]["gross"]["amount"] == undiscounted_subtotal_gross

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    assert order["order"]["deliveryMethod"]["id"] is not None

    shipping_price_gross = round(shipping_price_net * tax_rate, 2)
    shipping_tax = shipping_price_gross - shipping_price_net
    assert order["order"]["shippingPrice"]["net"]["amount"] == shipping_price_net
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price_gross
    undiscounted_total_net = round(undiscounted_subtotal_net + shipping_price_net, 2)

    undiscounted_total_gross = round(
        undiscounted_subtotal_gross + shipping_price_gross, 2
    )
    assert order["order"]["total"]["net"]["amount"] == undiscounted_total_net
    assert order["order"]["total"]["gross"]["amount"] == undiscounted_total_gross

    # Step 4 - Add voucher
    order = draft_order_update(
        e2e_staff_api_client, order_id, {"voucherCode": voucher_code}
    )

    assert order["order"]["voucherCode"] == voucher_code
    line_1_price_with_voucher_discount = product1_variant_price - voucher_discount_value
    order_line1 = order["order"]["lines"][0]
    assert (
        order_line1["unitPrice"]["net"]["amount"] == line_1_price_with_voucher_discount
    )
    assert order_line1["unitDiscountReason"] == f"Voucher code: {voucher_code}"

    line_2_price_with_voucher_discount = product2_variant_price - voucher_discount_value
    order_line2 = order["order"]["lines"][1]
    assert (
        order_line2["unitPrice"]["net"]["amount"] == line_2_price_with_voucher_discount
    )
    assert order_line2["unitDiscountReason"] == f"Voucher code: {voucher_code}"

    subtotal_net_with_voucher = undiscounted_subtotal_net - 2 * voucher_discount_value
    subtotal_gross_with_voucher = round(subtotal_net_with_voucher * tax_rate, 2)
    assert order["order"]["subtotal"]["net"]["amount"] == subtotal_net_with_voucher
    assert order["order"]["subtotal"]["gross"]["amount"] == subtotal_gross_with_voucher
    assert (
        order["order"]["subtotal"]["tax"]["amount"]
        == subtotal_gross_with_voucher - subtotal_net_with_voucher
    )

    # Step 5 - Add manual line discount
    manual_discount_value = 5
    manual_discount_reason = "Manual discount reason"
    assert manual_discount_value != voucher_discount_value
    manual_line_discount_input = {
        "valueType": "FIXED",
        "value": manual_discount_value,
        "reason": manual_discount_reason,
    }
    data = order_line_discount_update(
        e2e_staff_api_client, order_line1["id"], manual_line_discount_input
    )

    line_1_price_with_manual_discount = product1_variant_price - manual_discount_value
    order_line1 = data["order"]["lines"][0]
    assert (
        order_line1["unitPrice"]["net"]["amount"] == line_1_price_with_manual_discount
    )
    assert order_line1["unitPrice"]["gross"]["amount"] == round(
        line_1_price_with_manual_discount * tax_rate, 2
    )
    assert order_line1["unitDiscountReason"] == manual_discount_reason
    assert order_line1["unitDiscount"]["amount"] == manual_discount_value

    order_line2 = data["order"]["lines"][1]
    assert (
        order_line2["unitPrice"]["net"]["amount"] == line_2_price_with_voucher_discount
    )
    assert order_line2["unitPrice"]["gross"]["amount"] == round(
        line_2_price_with_voucher_discount * tax_rate, 2
    )

    subtotal_net = (
        line_1_price_with_manual_discount + line_2_price_with_voucher_discount
    )
    subtotal_gross = round(subtotal_net * tax_rate, 2)
    subtotal_tax = subtotal_gross - subtotal_net
    assert data["order"]["subtotal"]["net"]["amount"] == subtotal_net
    assert data["order"]["subtotal"]["gross"]["amount"] == subtotal_gross
    assert data["order"]["subtotal"]["tax"]["amount"] == subtotal_tax

    total_net = subtotal_net + shipping_price_net
    total_gross = subtotal_gross + shipping_price_gross
    total_tax = total_gross - total_net
    assert data["order"]["total"]["net"]["amount"] == total_net
    assert data["order"]["total"]["gross"]["amount"] == total_gross
    assert data["order"]["total"]["tax"]["amount"] == total_tax

    # Step 6 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    completed_order = order["order"]
    assert completed_order["status"] == "UNFULFILLED"
    assert completed_order["total"]["net"]["amount"] == total_net
    assert completed_order["total"]["gross"]["amount"] == total_gross
    assert completed_order["total"]["tax"]["amount"] == total_tax
    assert completed_order["subtotal"]["net"]["amount"] == subtotal_net
    assert completed_order["subtotal"]["gross"]["amount"] == subtotal_gross
    assert completed_order["subtotal"]["tax"]["amount"] == subtotal_tax
    assert completed_order["shippingPrice"]["net"]["amount"] == shipping_price_net
    assert completed_order["shippingPrice"]["gross"]["amount"] == shipping_price_gross
    assert completed_order["shippingPrice"]["tax"]["amount"] == shipping_tax
    assert (
        completed_order["lines"][0]["unitPrice"]["net"]["amount"]
        == product1_variant_price - manual_discount_value
    )
    assert completed_order["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        line_1_price_with_manual_discount * tax_rate, 2
    )
    assert (
        completed_order["lines"][0]["totalPrice"]["net"]["amount"]
        == product1_variant_price - manual_discount_value
    )
    assert completed_order["lines"][0]["totalPrice"]["gross"]["amount"] == round(
        line_1_price_with_manual_discount * tax_rate, 2
    )
    assert (
        completed_order["lines"][1]["unitPrice"]["net"]["amount"]
        == product2_variant_price - voucher_discount_value
    )
    assert completed_order["lines"][1]["unitPrice"]["gross"]["amount"] == round(
        line_2_price_with_voucher_discount * tax_rate, 2
    )
    assert (
        completed_order["lines"][1]["totalPrice"]["net"]["amount"]
        == product2_variant_price - voucher_discount_value
    )
    assert completed_order["lines"][1]["totalPrice"]["gross"]["amount"] == round(
        line_2_price_with_voucher_discount * tax_rate, 2
    )
