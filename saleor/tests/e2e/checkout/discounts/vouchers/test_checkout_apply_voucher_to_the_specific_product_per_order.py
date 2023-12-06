import pytest

from ....product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
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
)


def prepare_products(
    e2e_staff_api_client,
    warehouse_id,
    channel_id,
    first_product_variant_price,
    second_product_variant_price,
):
    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    first_product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    first_product_id = first_product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        first_product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    first_product_variant_data = create_product_variant(
        e2e_staff_api_client,
        first_product_id,
        stocks=stocks,
    )
    first_product_variant_id = first_product_variant_data["id"]

    first_product_variant_channel_listing_data = create_product_variant_channel_listing(
        e2e_staff_api_client,
        first_product_variant_id,
        channel_id,
        first_product_variant_price,
    )
    first_product_variant_price = first_product_variant_channel_listing_data[
        "channelListings"
    ][0]["price"]["amount"]

    second_product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    second_product_id = second_product_data["id"]

    create_product_channel_listing(
        e2e_staff_api_client,
        second_product_id,
        channel_id,
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    second_product_variant_data = create_product_variant(
        e2e_staff_api_client,
        second_product_id,
        stocks=stocks,
    )
    second_product_variant_id = second_product_variant_data["id"]

    second_product_variant_channel_listing_data = (
        create_product_variant_channel_listing(
            e2e_staff_api_client,
            second_product_variant_id,
            channel_id,
            second_product_variant_price,
        )
    )
    second_product_variant_price = second_product_variant_channel_listing_data[
        "channelListings"
    ][0]["price"]["amount"]

    return (
        first_product_id,
        first_product_variant_id,
        first_product_variant_price,
        second_product_variant_id,
        second_product_variant_price,
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
        "usageLimit": 2,
        "singleUse": True,
        "products": products,
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
def test_checkout_apply_voucher_to_the_specific_product_per_order_CORE_0915(
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
        first_product_id,
        first_product_variant_id,
        first_product_variant_price,
        second_product_variant_id,
        second_product_variant_price,
    ) = prepare_products(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        first_product_variant_price=15.00,
        second_product_variant_price=5.00,
    )

    voucher_code, voucher_id, voucher_discount_value = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        voucher_code="voucher",
        voucher_discount_type="FIXED",
        voucher_discount_value=2,
        voucher_type="SPECIFIC_PRODUCT",
        products=first_product_id,
    )

    # Step 1 - Create checkout for not logged in user
    lines = [
        {
            "variantId": first_product_variant_id,
            "quantity": 1,
        },
        {
            "variantId": second_product_variant_id,
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
    checkout_line = checkout["lines"]
    first_product_unit_price = float(first_product_variant_price)
    second_product_unit_price = float(second_product_variant_price)
    total_gross_amount = checkout["totalPrice"]["gross"]["amount"]
    assert checkout["isShippingRequired"] is True
    assert checkout_line[0]["variant"]["id"] == first_product_variant_id
    assert checkout_line[0]["unitPrice"]["gross"]["amount"] == first_product_unit_price
    assert (
        checkout_line[0]["undiscountedUnitPrice"]["amount"] == first_product_unit_price
    )
    assert checkout_line[1]["unitPrice"]["gross"]["amount"] == second_product_unit_price
    assert checkout_line[1]["variant"]["id"] == second_product_variant_id

    assert (
        checkout_line[1]["undiscountedUnitPrice"]["amount"] == second_product_unit_price
    )
    # Step 2 - Add voucher code to the checkout
    data = checkout_add_promo_code(
        e2e_not_logged_api_client,
        checkout_id,
        voucher_code,
    )
    discounted_total_gross = data["totalPrice"]["gross"]["amount"]
    discounted_first_product_unit_price = data["lines"][0]["unitPrice"]["gross"][
        "amount"
    ]
    undiscounted_second_product_unit_price = data["lines"][1]["unitPrice"]["gross"][
        "amount"
    ]
    discount_value = data["discount"]["amount"]
    assert (
        discounted_first_product_unit_price == first_product_unit_price - discount_value
    )
    assert discount_value == voucher_discount_value
    assert discounted_total_gross == round((total_gross_amount - discount_value), 2)
    assert (
        discounted_total_gross
        == discounted_first_product_unit_price + undiscounted_second_product_unit_price
    )

    # Step 3 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total = checkout_data["totalPrice"]["gross"]["amount"]
    assert total == shipping_price + discounted_total_gross

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total,
    )

    # Step 5 - Complete checkout
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)

    order_line = order_data["lines"]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total
    assert order_line[0]["undiscountedUnitPrice"]["gross"]["amount"] == float(
        first_product_variant_price
    )
    assert order_line[1]["undiscountedUnitPrice"]["gross"]["amount"] == float(
        second_product_variant_price
    )
    assert (
        order_line[0]["unitPrice"]["gross"]["amount"]
        == discounted_first_product_unit_price
    )
    assert (
        order_line[1]["unitPrice"]["gross"]["amount"]
        == undiscounted_second_product_unit_price
    )

    voucher_data = get_voucher(e2e_staff_api_client, voucher_id)
    assert voucher_data["voucher"]["id"] == voucher_id
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["isActive"] is False
    assert voucher_data["voucher"]["codes"]["edges"][0]["node"]["used"] == 1
