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
from ..utils import draft_order_create, draft_order_delete, order_query


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
        "usageLimit": None,
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

    return (
        voucher_code,
        voucher_id,
    )


@pytest.mark.e2e
def test_order_voucher_is_released_when_draft_order_is_deleted_CORE_0922(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
        permission_manage_checkouts,
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
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

    voucher_code, voucher_id = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="voucher",
        voucher_discount_type="PERCENTAGE",
        voucher_discount_value=15,
        voucher_type="ENTIRE_ORDER",
    )

    # Step 1 - Create draft order with the voucher
    input = {
        "channelId": channel_id,
        "userEmail": "test_user@test.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
        "lines": [{"variantId": product_variant_id, "quantity": 2}],
        "voucherCode": voucher_code,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert order_id is not None
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert data["order"]["lines"] is not None
    assert data["order"]["voucher"]["id"] == voucher_id

    # Step 2 - Delete order and verify the voucher can be used
    order = draft_order_delete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] is not None
    order = order_query(e2e_staff_api_client, order_id)
    assert order is None
    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"]["id"] == voucher_id
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 0
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is True
