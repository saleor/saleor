from ..channel.utils import create_channel
from ..products.utils import (
    create_category,
    create_digital_content,
    create_digital_product_type,
    create_product,
    create_product_channel_listing,
    create_product_variant,
)
from ..warehouse.utils import create_warehouse


def test_process_checkout_with_digital_product(
    api_client,
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
    media_root,
):
    channel_data = create_channel(staff_api_client, [permission_manage_channels])
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]
    assert channel_id is not None
    assert channel_slug is not None

    warehouse_data = create_warehouse(staff_api_client, [permission_manage_products])
    warehouse_id = warehouse_data["id"]
    assert warehouse_id is not None

    product_type_data = create_digital_product_type(
        staff_api_client, [permission_manage_product_types_and_attributes]
    )
    product_type_id = product_type_data["id"]
    assert product_type_id is not None

    category_data = create_category(staff_api_client, [permission_manage_products])
    category_id = category_data["id"]
    assert category_id is not None

    product_data = create_product(
        staff_api_client, [permission_manage_products], product_type_id, category_id
    )
    product_id = product_data["id"]
    assert product_id is not None

    product_channel_listing_data = create_product_channel_listing(
        staff_api_client, [permission_manage_products], product_id, channel_id
    )
    product_channel_listing_id = product_channel_listing_data["id"]
    assert product_channel_listing_id is not None

    product_variant_data = create_product_variant(
        staff_api_client, [permission_manage_products], product_id
    )
    product_variant_id = product_variant_data["id"]
    assert product_variant_id is not None

    digital_content_data = create_digital_content(staff_api_client, product_variant_id)
    digital_content_id = digital_content_data["id"]
    assert digital_content_id is not None
