import pytest

from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...shop.utils.preparing_shop import prepare_shop
from ...utils import assign_permissions
from ...vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_voucher,
)
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
)


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
        "usageLimit": 1,
        "singleUse": True,
        "applyOncePerOrder": True,
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

    return voucher_code, voucher_id, voucher_discount_value


@pytest.mark.e2e
def test_order_voucher_usage_includes_draft_orders_CORE_0913(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {"includeDraftOrderInVoucherUsage": True},
            }
        ],
    )
    channel_id = shop_data[0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

    voucher_code, voucher_id, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="voucher",
        voucher_discount_type="FIXED",
        voucher_discount_value=10,
        voucher_type="ENTIRE_ORDER",
    )

    # Step 1 - Create draft order with the voucher
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "userEmail": "test_user@test.com",
        "lines": [{"variantId": product_variant_id, "quantity": 2}],
        "voucherCode": voucher_code,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert order_id is not None
    subtotal_amount = float(product_variant_price)
    total_without_shipping = data["order"]["lines"][0]["totalPrice"]["gross"]["amount"]
    assert total_without_shipping == subtotal_amount * 2 - voucher_discount_value
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert data["order"]["lines"] is not None

    # Step 2 - Update the shipping method
    input = {"shippingMethod": shipping_method_id}
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    shipping_price = draft_order["order"]["shippingPrice"]["gross"]["amount"]
    total = draft_order["order"]["total"]["gross"]["amount"]
    discount_value = draft_order["order"]["voucher"]["discountValue"]
    assert draft_order["order"]["voucher"]["id"] == voucher_id
    assert discount_value == voucher_discount_value
    assert total == shipping_price + total_without_shipping
    assert order_shipping_id == shipping_method_id

    # Step 3 - Complete the order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    assert order["order"]["status"] == "UNFULFILLED"
    order_total = order["order"]["total"]["gross"]["amount"]
    assert order["order"]["voucher"]["id"] == voucher_id
    assert order_total == total

    # Step 4 - Verify the voucher's usage and status
    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"]["id"] == voucher_id
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is False
