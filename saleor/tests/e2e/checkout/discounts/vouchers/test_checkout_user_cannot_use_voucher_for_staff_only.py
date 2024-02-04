import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import create_voucher, create_voucher_channel_listing
from ...utils import checkout_create, raw_checkout_add_promo_code


def prepare_voucher_for_staff_only(
    e2e_staff_api_client,
    channel_id,
    voucher_code,
    voucher_discount_type,
    voucher_discount_value,
):
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": "ENTIRE_ORDER",
        "onlyForStaff": True,
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
def test_user_cannot_use_voucher_for_staff_only_in_checkout_core_0905(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before

    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
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
        variant_price="36.66",
    )

    voucher_discount_value, voucher_code = prepare_voucher_for_staff_only(
        e2e_staff_api_client,
        channel_id,
        "VOUCHER001",
        "PERCENTAGE",
        1,
    )

    # Step 1 - Create checkout for product on sale
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
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["unitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert checkout_data["isShippingRequired"] is True

    # Step 2 Add voucher code to checkout
    checkout_data = raw_checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    errors = checkout_data["errors"][0]
    assert errors["code"] == "VOUCHER_NOT_APPLICABLE"
    assert errors["field"] == "promoCode"
    assert errors["message"] == "Voucher is not applicable to this checkout."
