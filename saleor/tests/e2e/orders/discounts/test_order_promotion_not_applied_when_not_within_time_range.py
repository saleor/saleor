from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ... import DEFAULT_ADDRESS
from ...product.utils import get_product
from ...product.utils.preparing_product import prepare_product
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shop.utils.preparing_shop import prepare_shop
from ...utils import assign_permissions
from ..utils import draft_order_create


@freeze_time("2023-10-15 12:00:00")
@pytest.mark.e2e
def test_order_promotion_not_applied_when_not_within_time_range_CORE_2110(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
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

    (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

    (
        product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

    # Step 1 - Create promotion lasting for a specific time range
    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
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

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        catalogue_predicate,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
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
