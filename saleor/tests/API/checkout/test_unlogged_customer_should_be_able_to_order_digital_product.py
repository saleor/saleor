from ..channel.utils import create_channel
from ..products.utils import (
    create_digital_product_type,
    create_product,
    create_product_variant,
)
from ..warehouse.utils import create_warehouse


def test_process_checkout_with_digital_product(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    permission_manage_channels,
    permission_manage_products,
):
    channel_data = create_channel(staff_api_client, [permission_manage_channels])
    channel_id = channel_data["id"]
    assert channel_id is not None

    warehouse_data = create_warehouse(staff_api_client, [permission_manage_products])
    warehouse_id = warehouse_data["id"]
    assert warehouse_id is not None

    product_type_data = create_digital_product_type(
        staff_api_client, [permission_manage_product_types_and_attributes]
    )
    product_type_id = product_type_data["id"]
    assert product_type_id is not None

    product_data = create_product(
        staff_api_client, [permission_manage_products], product_type_id
    )
    product_id = product_data["id"]
    assert product_id is not None

    product_variant_data = create_product_variant(
        staff_api_client, [permission_manage_products], product_id
    )
    product_variant_id = product_variant_data["id"]
    assert product_variant_id is not None
