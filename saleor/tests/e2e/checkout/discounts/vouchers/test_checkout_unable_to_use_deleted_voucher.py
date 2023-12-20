import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_voucher,
    voucher_delete,
)
from ...utils import checkout_create, raw_checkout_add_promo_code


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
    voucher_type,
):
    input = {
        "addCodes": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": voucher_type,
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

    return voucher_id, voucher_code


@pytest.mark.e2e
def test_checkout_unable_to_use_deleted_voucher_CORE_0923(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=19.99,
    )

    voucher_id, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="FIXED_VOUCHER",
        voucher_discount_type="FIXED",
        voucher_discount_value=10,
        voucher_type="ENTIRE_ORDER",
    )

    # Step 1 - Delete voucher and verify it does not exist
    data = voucher_delete(e2e_staff_api_client, voucher_id)
    assert data["voucher"]["id"] == voucher_id

    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"] is None

    # Step 2 - Create checkout for not logged in user
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout["id"]
    checkout_lines = checkout["lines"][0]
    unit_price = float(product_variant_price)
    total_gross_amount = checkout["totalPrice"]["gross"]["amount"]
    assert checkout["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price
    assert total_gross_amount == unit_price

    # Step 3 - Add voucher code to the checkout
    data = raw_checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    errors = data["errors"][0]
    assert errors["code"] == "INVALID"
    assert errors["field"] == "promoCode"
    assert errors["message"] == "Promo code is invalid"
