import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_voucher,
    voucher_code_bulk_delete,
)
from ...utils import checkout_create, raw_checkout_add_promo_code


def create_voucher_with_multiple_codes(e2e_staff_api_client, channel_id):
    voucher_codes = []
    for i in range(10):
        voucher_codes.append(f"voucher_code_{i + 1}")

    input = {
        "addCodes": voucher_codes,
        "discountValueType": "PERCENTAGE",
        "type": "ENTIRE_ORDER",
    }
    voucher_data = create_voucher(e2e_staff_api_client, input)

    voucher_id = voucher_data["id"]
    voucher_code_ids_list = voucher_data["codes"]["edges"]
    voucher_data_code_ids = [edge["node"]["id"] for edge in voucher_code_ids_list]

    channel_listing = [
        {
            "channelId": channel_id,
            "discountValue": 25,
        },
    ]
    create_voucher_channel_listing(
        e2e_staff_api_client,
        voucher_id,
        channel_listing,
    )

    return voucher_id, voucher_data_code_ids


@pytest.mark.e2e
def test_checkout_unable_to_use_deleted_voucher_code_CORE_0914(
    e2e_staff_api_client,
    e2e_logged_api_client,
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
    (
        voucher_id,
        voucher_data_code_ids,
    ) = create_voucher_with_multiple_codes(e2e_staff_api_client, channel_id)

    # Step 1 - Delete voucher codes
    voucher_code_list_to_delete = voucher_data_code_ids[:5]
    data = voucher_code_bulk_delete(e2e_staff_api_client, voucher_code_list_to_delete)

    # Step 2 - Verify the voucher codes do not exist
    data = get_voucher(e2e_staff_api_client, voucher_id)
    response_voucher_codes = [
        edge["node"]["id"] for edge in data["voucher"]["codes"]["edges"]
    ]

    existing_voucher_codes = []
    non_existing_voucher_codes = []

    for voucher_code_id in voucher_code_list_to_delete:
        if voucher_code_id in response_voucher_codes:
            existing_voucher_codes.append(voucher_code_id)
        else:
            non_existing_voucher_codes.append(voucher_code_id)

    assert not existing_voucher_codes
    assert non_existing_voucher_codes == voucher_code_list_to_delete

    # Step 3 - Create checkout for logged in user
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout = checkout_create(
        e2e_logged_api_client,
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

    # Step 4 - Add deleted voucher code to the checkout
    voucher_code = voucher_code_list_to_delete[0]
    data = raw_checkout_add_promo_code(
        e2e_logged_api_client,
        checkout_id,
        voucher_code,
    )
    errors = data["errors"][0]
    assert errors["code"] == "INVALID"
    assert errors["field"] == "promoCode"
    assert errors["message"] == "Promo code is invalid"
