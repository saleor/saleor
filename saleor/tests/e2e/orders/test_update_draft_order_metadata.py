import pytest

from .. import DEFAULT_ADDRESS
from ..metadata.utils import (
    delete_metadata,
    delete_private_metadata,
    update_metadata,
    update_private_metadata,
)
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    order_lines_create,
    order_query,
    order_update_shipping,
)


@pytest.mark.e2e
def test_update_metadata_draft_order_CORE_0245(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
):
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    product_price = 33.33

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=product_price
    )

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add metadata to draft order
    metadata_input = [
        {"key": "metadataToBeUpdated", "value": "test value"},
        {"key": "metadataToBeRemoved", "value": "A"},
        {"key": "testEntityCode", "value": "A"},
    ]
    metadata = update_metadata(e2e_staff_api_client, order_id, metadata_input)
    assert len(metadata) == 3
    assert metadata[0]["key"] == "metadataToBeRemoved"
    assert metadata[0]["value"] == "A"
    assert metadata[1]["key"] == "metadataToBeUpdated"
    assert metadata[1]["value"] == "test value"
    assert metadata[2]["key"] == "testEntityCode"
    assert metadata[2]["value"] == "A"

    # Step 3 - Add order lines to the order
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    assert len(order["order"]["lines"]) == 1

    # Step 4 - Update draft order metadata value
    metadata_input = [{"key": "metadataToBeUpdated", "value": "updated value"}]
    metadata = update_metadata(e2e_staff_api_client, order_id, metadata_input)
    assert len(metadata) == 3
    assert metadata[0]["key"] == "metadataToBeRemoved"
    assert metadata[0]["value"] == "A"
    assert metadata[1]["key"] == "metadataToBeUpdated"
    assert metadata[1]["value"] == "updated value"
    assert metadata[2]["key"] == "testEntityCode"
    assert metadata[2]["value"] == "A"

    # Step 5 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    assert order["order"]["deliveryMethod"]["id"] is not None

    # Step 6 - Remove metadata from draft order
    metadata_to_remove = ["metadataToBeRemoved"]
    metadata = delete_metadata(e2e_staff_api_client, order_id, metadata_to_remove)
    assert len(metadata) == 2
    assert metadata[0]["key"] == "metadataToBeUpdated"
    assert metadata[0]["value"] == "updated value"
    assert metadata[1]["key"] == "testEntityCode"
    assert metadata[1]["value"] == "A"

    # Step 7 - Update private metadata
    private_metadata = [
        {"key": "privateMetadata", "value": "private value"},
        {"key": "privateMetadataToBeRemoved", "value": "private value"},
    ]
    private_metadata = update_private_metadata(
        e2e_staff_api_client, order_id, private_metadata
    )
    assert len(private_metadata) == 2
    assert private_metadata[0]["key"] == "privateMetadata"
    assert private_metadata[0]["value"] == "private value"
    assert private_metadata[1]["key"] == "privateMetadataToBeRemoved"
    assert private_metadata[1]["value"] == "private value"

    # Step 8 - Delete private metadata
    private_metadata_to_remove = ["privateMetadataToBeRemoved"]
    private_metadata = delete_private_metadata(
        e2e_staff_api_client, order_id, private_metadata_to_remove
    )
    assert len(private_metadata) == 1
    assert private_metadata[0]["key"] == "privateMetadata"
    assert private_metadata[0]["value"] == "private value"

    # Step 8 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)

    # Step 9 - Check if metadata is present in the order
    order = order_query(e2e_staff_api_client, order_id)
    metadata = order["metadata"]
    private_metadata = order["privateMetadata"]
    assert metadata[0]["key"] == "metadataToBeUpdated"
    assert metadata[0]["value"] == "updated value"
    assert metadata[1]["key"] == "testEntityCode"
    assert metadata[1]["value"] == "A"
    assert private_metadata[0]["key"] == "privateMetadata"
    assert private_metadata[0]["value"] == "private value"
