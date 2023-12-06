import pytest

from ....product.utils.preparing_product import prepare_product
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ....vouchers.utils import (
    create_voucher,
    create_voucher_channel_listing,
    get_voucher,
)
from ...utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    raw_checkout_add_promo_code,
)


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
        "usageLimit": 1,
        "singleUse": False,
        "products": products,
        "applyOncePerCustomer": True,
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
def test_checkout_with_voucher_limit_per_customer_CORE_0910(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
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
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=19.99,
    )

    voucher_code, voucher_id, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="FIXED",
        voucher_discount_type="FIXED",
        voucher_discount_value=10,
        voucher_type="SPECIFIC_PRODUCT",
        products=product_id,
    )

    # Step 1 - Create checkout
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
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == unit_price

    # Step 2 - Add voucher code to the checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    discounted_total_gross = data["totalPrice"]["gross"]["amount"]
    discounted_unit_price = data["lines"][0]["unitPrice"]["gross"]["amount"]
    discount_value = data["discount"]["amount"]
    discount_value = data["discount"]["amount"]
    assert discount_value == voucher_discount_value
    assert discounted_total_gross == round((total_gross_amount - discount_value), 2)

    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"]["id"] == voucher_id
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is True
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 0

    # Step 3 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)
    order_line = order_data["lines"][0]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert order_line["unitPrice"]["gross"]["amount"] == discounted_unit_price

    # Step 6 - Create checkout for the same user
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
    shipping_method_id = checkout["shippingMethods"][0]["id"]
    assert checkout["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price

    # Step 7 - Add the same voucher code to the checkout
    data = raw_checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    error = data["errors"][0]
    assert error["code"] == "INVALID"
    assert error["field"] == "promoCode"
    assert error["message"] == "Promo code is invalid"

    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"]["id"] == voucher_id
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is True
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1
