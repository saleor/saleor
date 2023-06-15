from ..channel.utils import create_channel
from ..products.utils import (
    create_category,
    create_digital_content,
    create_digital_product_type,
    create_product,
    create_product_channel_listing,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..shipping_zone.utils import create_shipping_zone
from ..warehouse.utils import create_warehouse
from .utils import (
    checkout_billing_address_update,
    checkout_complete,
    checkout_create,
    checkout_payment_create,
)


def test_process_checkout_with_digital_product(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
    permission_manage_shipping,
    media_root,
):
    # given
    warehouse_data = create_warehouse(staff_api_client, [permission_manage_products])
    warehouse_id = warehouse_data["id"]

    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        staff_api_client, [permission_manage_channels], warehouse_ids
    )
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]

    channel_ids = [channel_id]
    create_shipping_zone(
        staff_api_client, [permission_manage_shipping], warehouse_ids, channel_ids
    )

    product_type_data = create_digital_product_type(
        staff_api_client, [permission_manage_product_types_and_attributes]
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(staff_api_client, [permission_manage_products])
    category_id = category_data["id"]

    product_data = create_product(
        staff_api_client, [permission_manage_products], product_type_id, category_id
    )
    product_id = product_data["id"]

    create_product_channel_listing(
        staff_api_client, [permission_manage_products], product_id, channel_id
    )

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        staff_api_client,
        [permission_manage_products],
        product_id,
        stocks,
    )
    product_variant_id = product_variant_data["id"]

    create_product_variant_channel_listing(
        staff_api_client,
        [permission_manage_products],
        product_variant_id,
        channel_id,
    )

    create_digital_content(staff_api_client, product_variant_id)

    # when
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(api_client, lines, channel_slug)
    checkout_id = checkout_data["id"]
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    checkout_billing_address_update(api_client, checkout_id)

    checkout_payment_create(api_client, checkout_id, total_gross_amount)

    order_data = checkout_complete(api_client, checkout_id)

    # then
    assert order_data["isShippingRequired"] is False
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
