from ...channel.utils import create_channel
from ...shipping_zone.utils.shipping_method import create_shipping_method
from ...shipping_zone.utils.shipping_method_channel_listing import (
    create_shipping_method_channel_listing,
)
from ...shipping_zone.utils.shipping_zone import create_shipping_zone
from ...warehouse.utils import create_warehouse


def prepare_shop(e2e_staff_api_client):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    channel_slug = "test"
    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
        warehouse_ids=warehouse_ids,
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
        e2e_staff_api_client,
        shipping_zone_id,
    )
    shipping_method_id = shipping_method_data["id"]
    create_shipping_method_channel_listing(
        e2e_staff_api_client,
        shipping_method_id,
        channel_id,
    )
    return (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_method_id,
    )
