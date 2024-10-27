import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ...vouchers.utils import (
    add_catalogue_to_voucher,
    create_voucher,
    create_voucher_channel_listing,
)
from ..utils import (
    checkout_add_promo_code,
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_lines_add,
)


def prepare_promotion(
    e2e_staff_api_client,
    product_id,
    channel_id,
    promotion_value,
    promotion_value_type,
):
    promotion_name = "test_promotion"
    promotion_type = "CATALOGUE"

    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
        promotion_type,
    )
    promotion_id = promotion_data["id"]

    assert promotion_id is not None

    promotion_rule_name = "test_promotion_rule"

    catalogue_predicate = {
        "productPredicate": {"ids": [product_id]},
    }
    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": promotion_value,
        "rewardValueType": promotion_value_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    return (
        promotion_id,
        promotion_value,
    )


def prepare_voucher(
    e2e_staff_api_client,
    channel_id,
    product_id,
    voucher_discount_type,
    voucher_discount_value,
):
    voucher_code = "test_voucher"
    input = {
        "code": voucher_code,
        "discountValueType": voucher_discount_type,
        "type": "ENTIRE_ORDER",
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

    add_catalogue_to_voucher(
        e2e_staff_api_client,
        voucher_id,
        include_products=True,
        products=[product_id],
    )

    return voucher_discount_value, voucher_code


@pytest.mark.e2e
@pytest.mark.parametrize(
    (
        "variant_price",
        "promotion_value",
        "promotion_value_type",
        "expected_promotion_discount",
        "voucher_discount_value",
        "voucher_discount_type",
        "expected_voucher_discount",
        "expected_unit_price",
    ),
    [
        ("19.99", 13, "PERCENTAGE", 2.60, 13, "PERCENTAGE", 2.26, 15.13),
        ("30", 10, "FIXED", 10, 5, "FIXED", 5, 17.5),
        ("56.50", 19.99, "FIXED", 19.99, 33, "PERCENTAGE", 12.05, 24.46),
        ("77.77", 17.5, "PERCENTAGE", 13.61, 25, "FIXED", 25, 51.66),
    ],
)
def test_checkout_with_promotion_and_voucher_CORE_2107(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    variant_price,
    promotion_value_type,
    promotion_value,
    expected_promotion_discount,
    voucher_discount_value,
    voucher_discount_type,
    expected_voucher_discount,
    expected_unit_price,
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
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    promotion_id, promotion_value = prepare_promotion(
        e2e_staff_api_client,
        product_id,
        channel_id,
        promotion_value,
        promotion_value_type,
    )

    voucher_discount_value, voucher_code = prepare_voucher(
        e2e_staff_api_client,
        channel_id,
        product_id,
        voucher_discount_type,
        voucher_discount_value,
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Create checkout for product with promotion
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
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

    assert checkout_data["isShippingRequired"] is True
    unit_price_with_promotion = round(
        float(product_variant_price - expected_promotion_discount), 2
    )
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price_with_promotion
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == product_variant_price

    # Step 2 Add voucher code to checkout
    checkout_data = checkout_add_promo_code(
        e2e_not_logged_api_client, checkout_id, voucher_code
    )
    assert checkout_data["discount"]["amount"] == expected_voucher_discount
    assert checkout_data["lines"][0]["unitPrice"]["gross"]["amount"] == round(
        float(unit_price_with_promotion - expected_voucher_discount), 2
    )

    # Step 3 Add variant to the checkout
    lines_add = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_lines_add(
        e2e_staff_api_client,
        checkout_id,
        lines_add,
    )
    checkout_lines = checkout_data["lines"][0]
    assert checkout_lines["quantity"] == 2
    assert checkout_lines["unitPrice"]["gross"]["amount"] == expected_unit_price
    subtotal_amount = expected_unit_price * 2
    assert checkout_lines["totalPrice"]["gross"]["amount"] == subtotal_amount

    # Step 4 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    shipping_price = checkout_data["deliveryMethod"]["price"]["amount"]
    total_gross_amount = round(subtotal_amount + shipping_price, 2)
    assert checkout_data["totalPrice"]["gross"]["amount"] == total_gross_amount

    # Step 5 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 6 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["discounts"][0]["type"] == "VOUCHER"
    assert order_data["voucher"]["code"] == voucher_code

    order_line = order_data["lines"][0]
    assert order_line["unitDiscountType"] == "FIXED"
    assert order_line["unitPrice"]["gross"]["amount"] == expected_unit_price
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["subtotal"]["gross"]["amount"] == subtotal_amount
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert order_line["unitDiscountReason"] == (
        f"Entire order voucher code: {voucher_code} & Promotion: {promotion_id}"
    )
