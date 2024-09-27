from decimal import Decimal

import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ...vouchers.utils import create_voucher, create_voucher_channel_listing
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_discount_add,
    order_lines_create,
)


def prepare_shipping_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": "SHIPPING",
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)
    voucher_id = voucher_data["id"]
    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": voucher_discount_value,
        }
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_discount_value, voucher_code


@pytest.mark.e2e
def test_order_with_shipping_voucher_and_manual_order_discount_CORE_0249(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]
    undiscounted_shipping_price = Decimal(10)
    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=Decimal(15),
    )

    voucher_code = "free-shipping"
    voucher_discount_value = Decimal(50)
    prepare_shipping_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code,
        "PERCENTAGE",
        voucher_discount_value,
    )

    # Step 1 - Create a draft order with shipping voucher
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
        "voucherCode": voucher_code,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert data["order"]["voucher"]["code"] == voucher_code

    # Step 2 - Add order line
    quantity = 3
    lines = [{"variantId": product_variant_id, "quantity": quantity}]
    data = order_lines_create(e2e_staff_api_client, order_id, lines)
    undiscounted_subtotal = Decimal(quantity * product_variant_price)
    undiscounted_total = undiscounted_subtotal + undiscounted_shipping_price

    assert data["order"]["subtotal"]["gross"]["amount"] == undiscounted_subtotal
    # TODO (SHOPX-1388): Shipping price is not updated when running `orderLinesCreate`
    # assert undiscounted_shipping_price == data["order"]["undiscountedShippingPrice"]["amount"]

    # Step 3 - Add shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    data = draft_order_update(e2e_staff_api_client, order_id, input)
    assert (
        undiscounted_shipping_price
        == data["order"]["undiscountedShippingPrice"]["amount"]
    )
    shipping_price = Decimal(data["order"]["shippingPrice"]["gross"]["amount"])
    assert shipping_price == undiscounted_shipping_price * voucher_discount_value / 100
    voucher_discount_amount = undiscounted_shipping_price - shipping_price
    subtotal = Decimal(data["order"]["subtotal"]["gross"]["amount"])
    assert undiscounted_subtotal == subtotal
    total = Decimal(data["order"]["total"]["gross"]["amount"])
    assert total == undiscounted_total - voucher_discount_amount

    # Step 4 - Add manual discount to the order
    manual_discount_value = Decimal(15)
    manual_discount_input = {
        "valueType": "FIXED",
        "value": manual_discount_value,
    }
    data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        manual_discount_input,
    )
    manual_discount_subtotal_share = Decimal(subtotal / total * manual_discount_value)
    manual_discount_shipping_share = (
        manual_discount_value - manual_discount_subtotal_share
    )
    shipping_price = Decimal(data["order"]["shippingPrice"]["gross"]["amount"])

    assert (
        shipping_price
        == undiscounted_shipping_price * voucher_discount_value / 100
        - manual_discount_shipping_share
    )
    subtotal = Decimal(data["order"]["subtotal"]["gross"]["amount"])
    assert subtotal == undiscounted_subtotal - manual_discount_subtotal_share
    total = Decimal(data["order"]["total"]["gross"]["amount"])
    assert total == undiscounted_total - voucher_discount_amount - manual_discount_value

    # Step 5 - Complete the draft order
    data = draft_order_complete(e2e_staff_api_client, order_id)
    assert (
        Decimal(data["order"]["undiscountedShippingPrice"]["amount"])
        == undiscounted_shipping_price
    )
    assert Decimal(data["order"]["shippingPrice"]["gross"]["amount"]) == shipping_price
    assert Decimal(data["order"]["subtotal"]["gross"]["amount"]) == subtotal
    assert (
        Decimal(data["order"]["undiscountedTotal"]["gross"]["amount"])
        == undiscounted_total
    )
    assert Decimal(data["order"]["total"]["gross"]["amount"]) == total

    order_line = data["order"]["lines"][0]
    assert (
        order_line["undiscountedUnitPrice"]["gross"]["amount"] == product_variant_price
    )
    assert order_line["unitPrice"]["gross"]["amount"] == Decimal(
        product_variant_price
    ) - Decimal(manual_discount_subtotal_share / quantity)
