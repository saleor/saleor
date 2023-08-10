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
)
from ..promotions.utils import create_promotion, create_promotion_rule
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse, update_warehouse
from .utils.draft_order_complete import draft_order_complete
from .utils.draft_order_create import draft_order_create
from .utils.draft_order_update import draft_order_update
from .utils import order_lines_create


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
    promotion_name,
    discount_value,
    discount_type,
    promotion_rule_name,
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

    promotion_data = create_promotion(e2e_staff_api_client, promotion_name)
    promotion_id = promotion_data["id"]

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
        product_id,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    return channel_id, product_variant_id, shipping_method_id


@pytest.mark.e2e
def test_order_products_on_fixed_promotion_CORE_2101(
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

    (
        channel_id,
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
        promotion_name,
        discount_value,
        discount_type,
        promotion_rule_name,
    )

    # Step 1 - Create a draft order for a product with fixed promotion
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
        "shippingMethod": shipping_method_id,
        "lines": lines,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    order_shipping_method_id = data["order"]["shippingMethods"][0]["id"]
    unit_price = float(variant_price) - float(discount_value)
    undiscounted_price = data["order"]["lines"][0]["undiscountedUnitPrice"]["gross"][
        "amount"
    ]
    assert float(undiscounted_price) == float(variant_price)
    assert data["order"]["lines"][0]["unitPrice"]["gross"]["amount"] == unit_price
    print(data)
    # UNCOMMENT WHEN https://github.com/saleor/saleor/issues/13675 is resolved:
    # assert order_shipping_method_id == shipping_method_id
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id
    print(order_lines)

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    draft_update = draft_order_update(e2e_staff_api_client, order_id, input)
    order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    shipping_price = draft_update["order"]["shippingPrice"]["gross"]["amount"]
    subtotal_gross_amount = draft_update["order"]["subtotal"]["gross"]["amount"]
    total_gross_amount = draft_update["order"]["total"]["gross"]["amount"]
    assert order_shipping_method_id == order_shipping_id
    print(draft_update)

    # Step 4 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    assert order_line["unitDiscount"]["amount"] == float(discount_value)
    assert order_line["unitDiscountType"] == discount_type
    assert order_line["unitDiscountValue"] == float(discount_value)
    product_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert product_price == float(undiscounted_price)
    assert product_price == float(variant_price)
    total = order["order"]["total"]["gross"]["amount"]
    assert total == float(total_gross_amount)
    subtotal = order["order"]["subtotal"]["gross"]["amount"]
    assert subtotal == subtotal_gross_amount
    shipping_amount = order["order"]["shippingPrice"]["gross"]["amount"]
    assert shipping_amount == shipping_price
    assert shipping_amount + subtotal == total
    assert order["order"]["status"] == "UNFULFILLED"
