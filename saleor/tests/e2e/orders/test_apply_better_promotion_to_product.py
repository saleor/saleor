import pytest

from .. import DEFAULT_ADDRESS
from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    get_product,
)
from ..promotions.utils import create_promotion, create_promotion_rule
from ..utils import assign_permissions
from .utils import draft_order_create, order_lines_create


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
    channel_slug,
    variant_price,
    first_promotion_name,
    first_discount_value,
    first_discount_type,
    first_rule_name,
    second_promotion_name,
    second_discount_value,
    second_discount_type,
    second_rule_name,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
    )
    channel_id = channel_data["id"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    variant_data = create_product_variant(e2e_staff_api_client, product_id)
    product_variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )

    first_promotion = create_promotion(e2e_staff_api_client, first_promotion_name)
    promotion_id = first_promotion["id"]

    first_promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        first_discount_type,
        first_discount_value,
        first_rule_name,
        channel_id,
        product_id,
    )
    product_predicate = first_promotion_rule["cataloguePredicate"]["productPredicate"][
        "ids"
    ]
    assert first_promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    second_promotion = create_promotion(e2e_staff_api_client, second_promotion_name)
    promotion_id = second_promotion["id"]

    second_promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        second_discount_type,
        second_discount_value,
        second_rule_name,
        channel_id,
        product_id,
    )
    product_predicate = second_promotion_rule["cataloguePredicate"]["productPredicate"][
        "ids"
    ]
    assert second_promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    return product_id, channel_id, product_variant_id


@pytest.mark.e2e
def test_apply_best_promotion_to_product_core_2105(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    channel_slug = "test-channel"
    variant_price = "30"
    first_promotion_name = "Promotion Fixed"
    first_discount_value = 5.5
    first_discount_type = "FIXED"
    first_rule_name = "rule for product"

    second_promotion_name = "Promotion Percentage"
    second_discount_value = 20
    second_discount_type = "PERCENTAGE"
    second_rule_name = "rule for product"

    product_id, channel_id, product_variant_id = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
        channel_slug,
        variant_price,
        first_promotion_name,
        first_discount_value,
        first_discount_type,
        first_rule_name,
        second_promotion_name,
        second_discount_value,
        second_discount_type,
        second_rule_name,
    )

    # Step 1 - Get product and check if it is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)

    assert product_data["pricing"]["onSale"] is True
    second_variant_discount = round(
        float(variant_price) * second_discount_value / 100, 2
    )
    product_variant = product_data["variants"][0]
    assert product_data["pricing"]["onSale"] is True
    assert product_variant["pricing"]["onSale"] is True
    assert (
        product_variant["pricing"]["discount"]["gross"]["amount"]
        == second_variant_discount
    )
    assert product_variant["pricing"]["priceUndiscounted"]["gross"]["amount"] == float(
        variant_price
    )

    # Step 2 - Create draft order
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    order_data = draft_order_create(e2e_staff_api_client, input)

    order_id = order_data["order"]["id"]
    assert order_data["order"]["billingAddress"] is not None
    assert order_data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 3 - Add product to order and verify prices
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)

    order_line = order_lines["order"]["lines"][0]
    assert order_line["variant"]["id"] == product_variant_id
    unit_price = float(variant_price) - second_variant_discount
    undiscounted_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert float(undiscounted_price) == float(variant_price)
    assert order_line["unitPrice"]["gross"]["amount"] == unit_price
    promotion_reason = order_line["unitDiscountReason"]
    assert (
        promotion_reason
        == f"Promotion rules discounts: {second_promotion_name}: {second_rule_name}"
    )
