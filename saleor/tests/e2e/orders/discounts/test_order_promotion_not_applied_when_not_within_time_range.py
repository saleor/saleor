from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils import get_product
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ..utils import draft_order_create


@freeze_time("2023-10-15 12:00:00")
@pytest.mark.e2e
def test_order_promotion_not_applied_when_not_within_time_range_CORE_2110(
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

    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"
    today = timezone.now()
    tomorrow = today + timedelta(days=1)
    month_after = today + timedelta(days=30)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Create promotion lasting for a specific time range
    promotion_type = "CATALOGUE"
    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
        promotion_type,
        start_date=tomorrow,
        end_date=month_after,
    )
    promotion_id = promotion_data["id"]
    promotion_start_date = promotion_data["startDate"]
    promotion_end_date = promotion_data["endDate"]

    assert promotion_id is not None
    assert promotion_start_date == tomorrow.isoformat()
    assert promotion_end_date == month_after.isoformat()

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
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

    # Step 2 - Get product and check if it is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is False
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is False

    # Step 3 - Create a draft order and check no discounts have been applied
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
        "lines": [{"variantId": product_variant_id, "quantity": 2}],
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert order_id is not None
    order_create_date = data["order"]["created"]
    assert order_create_date == today.isoformat()
    assert today != tomorrow
    assert today != month_after
    assert data["order"]["discounts"] == []
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert data["order"]["lines"] is not None
