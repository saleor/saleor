import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils import get_product
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ..utils import draft_order_create, order_lines_create


def prepare_promotion_with_rules(
    e2e_staff_api_client,
    promotion_name,
    discount_type,
    discount_value,
    rule_name,
    channel_id,
    product_id,
):
    promotion_type = "CATALOGUE"
    promotion = create_promotion(e2e_staff_api_client, promotion_name, promotion_type)
    promotion_id = promotion["id"]

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}
    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id
    return promotion_id


@pytest.mark.e2e
@pytest.mark.parametrize(
    (
        "variant_price",
        "first_discount_type",
        "first_discount_value",
        "second_discount_type",
        "second_discount_value",
        "expected_discount",
    ),
    [
        ("30", "FIXED", 5.50, "PERCENTAGE", 20, 6.00),
        ("30", "PERCENTAGE", 11, "PERCENTAGE", 13, 3.90),
        ("30", "FIXED", 5.99, "FIXED", 6.00, 6.00),
    ],
)
def test_apply_best_promotion_to_product_core_2105(
    variant_price,
    first_discount_type,
    first_discount_value,
    second_discount_type,
    second_discount_value,
    expected_discount,
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

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    product_id, product_variant_id, product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    # Create first promotion
    first_promotion_name = "Promotion 1"
    first_rule_name = "rule for product"

    prepare_promotion_with_rules(
        e2e_staff_api_client,
        first_promotion_name,
        first_discount_type,
        first_discount_value,
        first_rule_name,
        channel_id,
        product_id,
    )

    # Create second promotion
    second_promotion_name = "Promotion 2"
    second_rule_name = "rule for product"

    second_promotion_id = prepare_promotion_with_rules(
        e2e_staff_api_client,
        second_promotion_name,
        second_discount_type,
        second_discount_value,
        second_rule_name,
        channel_id,
        product_id,
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Get product and check if it is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)

    assert product_data["pricing"]["onSale"] is True

    product_variant = product_data["variants"][0]
    assert product_variant["pricing"]["onSale"] is True
    assert (
        product_variant["pricing"]["discount"]["gross"]["amount"] == expected_discount
    )
    assert product_variant["pricing"]["priceUndiscounted"]["gross"]["amount"] == float(
        product_variant_price
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
    unit_price = float(product_variant_price) - expected_discount
    undiscounted_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert undiscounted_price == float(product_variant_price)
    assert order_line["unitPrice"]["gross"]["amount"] == unit_price
    promotion_reason = order_line["unitDiscountReason"]
    assert promotion_reason == f"Promotion: {second_promotion_id}"
