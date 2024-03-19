import pytest

from .....product.tasks import recalculate_discounted_price_for_products_task
from ... import DEFAULT_ADDRESS
from ...product.utils.preparing_product import prepare_product
from ...sales.utils import create_sale, create_sale_channel_listing, sale_catalogues_add
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions
from ..utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
)


def prepare_sale_for_product(
    e2e_staff_api_client,
    channel_id,
    product_id,
    sale_discount_type,
    sale_discount_value,
):
    sale_name = "Sale"
    sale = create_sale(
        e2e_staff_api_client,
        sale_name,
        sale_discount_type,
    )
    sale_id = sale["id"]
    sale_listing_input = [
        {
            "channelId": channel_id,
            "discountValue": sale_discount_value,
        }
    ]
    create_sale_channel_listing(
        e2e_staff_api_client,
        sale_id,
        add_channels=sale_listing_input,
    )
    catalogue_input = {"products": [product_id]}
    sale_catalogues_add(
        e2e_staff_api_client,
        sale_id,
        catalogue_input,
    )

    return sale_id, sale_discount_value


@pytest.mark.e2e
def test_order_products_on_fixed_sale_CORE_1001(
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
        variant_price="41.99",
    )

    sale_id, sale_discount_value = prepare_sale_for_product(
        e2e_staff_api_client,
        channel_id,
        product_id,
        sale_discount_type="FIXED",
        sale_discount_value=30,
    )

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        input,
    )
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add product on sale to draft order
    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )

    draft_line = order_lines["order"]["lines"][0]
    assert draft_line["variant"]["id"] == product_variant_id
    unit_price = float(product_variant_price) - float(sale_discount_value)
    undiscounted_price = draft_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert undiscounted_price == float(product_variant_price)
    assert draft_line["unitPrice"]["gross"]["amount"] == round(unit_price, 2)

    # Step 3 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    draft_update = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )

    order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    assert order_shipping_id is not None
    shipping_price = draft_update["order"]["shippingPrice"]["gross"]["amount"]

    # Step 4 - Complete the draft order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    total = order["order"]["total"]["gross"]["amount"]
    assert total == round(float(shipping_price + unit_price), 2)

    order_line = order["order"]["lines"][0]
    assert order_line["unitDiscount"]["amount"] == sale_discount_value
    assert order_line["unitDiscountValue"] == sale_discount_value
    assert order_line["unitDiscountType"] == "FIXED"
    assert draft_line["unitDiscountReason"] == f"Sale: {sale_id}"
    product_price = order_line["undiscountedUnitPrice"]["gross"]["amount"]
    assert product_price == undiscounted_price
