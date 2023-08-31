from datetime import datetime, timedelta

import pytest
from dateutil.tz import tzlocal

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
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse, update_warehouse
from .utils import draft_order_create


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
    channel_slug,
    variant_price,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    update_warehouse(
        e2e_staff_api_client,
        warehouse_data["id"],
        is_private=False,
    )
    warehouse_ids = [warehouse_id]

    channel_data = create_channel(
        e2e_staff_api_client,
        warehouse_ids,
        slug=channel_slug,
    )
    channel_id = channel_data["id"]
    channel_ids = [channel_id]

    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, shipping_method_id, channel_id
    )

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

    stocks = [
        {
            "warehouse": warehouse_data["id"],
            "quantity": 5,
        }
    ]
    variant_data = create_product_variant(
        e2e_staff_api_client, product_id, stocks=stocks
    )
    product_variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
        variant_price,
    )

    return channel_id, product_id, product_variant_id, shipping_method_id


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
    channel_slug = "test-channel"
    variant_price = "20"
    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"
    today = datetime.now(tzlocal()).isoformat()
    tomorrow = (datetime.now(tzlocal()) + timedelta(days=1)).isoformat()
    month_after = (datetime.now(tzlocal()) + timedelta(days=30)).isoformat()

    (
        channel_id,
        product_id,
        product_variant_id,
        shipping_method_id,
    ) = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
        channel_slug,
        variant_price,
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
    assert promotion_start_date == tomorrow
    assert promotion_end_date == month_after

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
    today = datetime.now(tzlocal()).isoformat().split("T")[0]
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert order_id is not None
    order_create_date = data["order"]["created"]
    order_datetime = datetime.strptime(order_create_date, "%Y-%m-%dT%H:%M:%S.%f%z")
    order_date_formatted = order_datetime.date().isoformat().split("T")[0]
    assert order_date_formatted == today
    assert today != tomorrow
    assert today != month_after
    assert data["order"]["discounts"] == []
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert data["order"]["lines"] is not None
