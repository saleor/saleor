import graphene

from . import PRIVATE_KEY, PRIVATE_VALUE, PUBLIC_KEY, PUBLIC_VALUE
from .test_delete_metadata import (
    execute_clear_public_metadata_for_item,
    item_without_public_metadata,
)
from .test_delete_private_metadata import (
    execute_clear_private_metadata_for_item,
    item_without_private_metadata,
)
from .test_update_metadata import (
    execute_update_public_metadata_for_item,
    item_contains_proper_public_metadata,
)
from .test_update_private_metadata import (
    execute_update_private_metadata_for_item,
    item_contains_proper_private_metadata,
)


def test_delete_private_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse.store_value_in_private_metadata({PRIVATE_KEY: PRIVATE_VALUE})
    warehouse.save(update_fields=["private_metadata"])
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"], warehouse, warehouse_id
    )


def test_delete_public_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    warehouse.save(update_fields=["metadata"])
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"], warehouse, warehouse_id
    )


def test_add_public_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"], warehouse, warehouse_id
    )


def test_add_private_metadata_for_warehouse(
    staff_api_client, permission_manage_products, warehouse
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client, permission_manage_products, warehouse_id, "Warehouse"
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"], warehouse, warehouse_id
    )
