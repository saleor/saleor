import pytest

from ... import DEFAULT_ADDRESS
from ...channel.utils import create_channel
from ...product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ...promotions.utils import create_promotion, create_promotion_rule
from ...shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ...utils import assign_permissions
from ...warehouse.utils import create_warehouse, update_warehouse
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
    channel_slug,
    variant_price_1,
    variant_price_2,
    promotion_name,
    discount_value,
    discount_type,
    promotion_rule_name,
):
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
    category_ids = [category_id]

    product_data_1 = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id_1 = product_data_1["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id_1, channel_id)

    stocks = [
        {
            "warehouse": warehouse_data["id"],
            "quantity": 5,
        }
    ]
    variant_data_1 = create_product_variant(
        e2e_staff_api_client, product_id_1, stocks=stocks
    )
    product_variant_id_1 = variant_data_1["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id_1,
        channel_id,
        variant_price_1,
    )
    product_data_2 = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id_2 = product_data_2["id"]
    create_product_channel_listing(e2e_staff_api_client, product_id_2, channel_id)

    stocks = [
        {
            "warehouse": warehouse_data["id"],
            "quantity": 5,
        }
    ]
    variant_data_2 = create_product_variant(
        e2e_staff_api_client, product_id_2, stocks=stocks
    )
    product_variant_id_2 = variant_data_2["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id_2,
        channel_id,
        variant_price_2,
    )

    promotion_data = create_promotion(e2e_staff_api_client, promotion_name)
    promotion_id = promotion_data["id"]

    catalogue_predicate = {
        "categoryPredicate": {"ids": category_ids},
    }

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        catalogue_predicate,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
    )
    category_predicate = promotion_rule["cataloguePredicate"]["categoryPredicate"][
        "ids"
    ]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert category_predicate[0] == category_id

    return (
        channel_id,
        product_variant_id_1,
        product_variant_id_2,
        shipping_method_id,
        promotion_id,
    )


@pytest.mark.e2e
def test_order_products_from_category_on_fixed_promotion_CORE_2106(
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

    channel_slug = "test-channel"
    variant_price_1 = "20"
    variant_price_2 = "10"
    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for category"
    (
        channel_id,
        product_variant_id_1,
        product_variant_id_2,
        shipping_method_id,
        promotion_id,
    ) = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
        channel_slug,
        variant_price_1,
        variant_price_2,
        promotion_name,
        discount_value,
        discount_type,
        promotion_rule_name,
    )

    # Step 1 - Create a draft order for a product with fixed promotion
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product_variant_id_1, "quantity": 2},
        {"variantId": product_variant_id_2, "quantity": 2},
    ]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product_variant_id_1 = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id_1 == product_variant_id_1
    unit_price_product_1 = float(variant_price_1) - float(discount_value)
    undiscounted_price_product_1 = order_lines["order"]["lines"][0][
        "undiscountedUnitPrice"
    ]["gross"]["amount"]
    assert float(undiscounted_price_product_1) == float(variant_price_1)
    assert (
        order_lines["order"]["lines"][0]["unitPrice"]["gross"]["amount"]
        == unit_price_product_1
    )
    order_product_variant_id_2 = order_lines["order"]["lines"][1]["variant"]["id"]
    assert order_product_variant_id_2 == product_variant_id_2
    unit_price_product_2 = float(variant_price_2) - float(discount_value)
    undiscounted_price_product_2 = order_lines["order"]["lines"][1][
        "undiscountedUnitPrice"
    ]["gross"]["amount"]
    assert float(undiscounted_price_product_2) == float(variant_price_2)
    assert (
        order_lines["order"]["lines"][1]["unitPrice"]["gross"]["amount"]
        == unit_price_product_2
    )

    promotion_reason = order_lines["order"]["lines"][0]["unitDiscountReason"]
    assert promotion_reason == f"Promotion: {promotion_id}"

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    draft_update = draft_order_update(e2e_staff_api_client, order_id, input)
    order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    shipping_price = draft_update["order"]["shippingPrice"]["gross"]["amount"]
    subtotal_gross_amount = draft_update["order"]["subtotal"]["gross"]["amount"]
    total_gross_amount = draft_update["order"]["total"]["gross"]["amount"]
    assert order_shipping_id is not None

    # Step 4 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line_1 = order["order"]["lines"][0]
    assert order_line_1["productVariantId"] == product_variant_id_1
    assert order_line_1["unitDiscount"]["amount"] == float(discount_value)
    assert order_line_1["unitDiscountType"] == discount_type
    assert order_line_1["unitDiscountValue"] == float(discount_value)
    assert order_line_1["unitDiscountReason"] == promotion_reason
    order_line_2 = order["order"]["lines"][1]
    assert order_line_2["productVariantId"] == product_variant_id_2
    assert order_line_2["unitDiscount"]["amount"] == float(discount_value)
    assert order_line_2["unitDiscountType"] == discount_type
    assert order_line_2["unitDiscountValue"] == float(discount_value)
    assert order_line_2["unitDiscountReason"] == promotion_reason
    shipping_amount = order["order"]["shippingPrice"]["gross"]["amount"]
    assert shipping_amount == shipping_price
    subtotal = unit_price_product_1 * 2 + unit_price_product_2 * 2
    assert subtotal == order["order"]["subtotal"]["gross"]["amount"]
    assert subtotal == subtotal_gross_amount
    total = shipping_amount + subtotal
    assert total == order["order"]["total"]["gross"]["amount"]
    assert total == float(total_gross_amount)

    assert order["order"]["status"] == "UNFULFILLED"
