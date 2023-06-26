import graphene

from . import PUBLIC_KEY, PUBLIC_VALUE
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


def test_delete_private_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_method.save(update_fields=["metadata"])
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_delete_private_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_zone.save(update_fields=["metadata"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )


def test_delete_public_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_method.save(update_fields=["metadata"])
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_delete_public_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    shipping_zone.save(update_fields=["metadata"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )


def test_add_public_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_add_public_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )


def test_add_private_metadata_for_shipping_method(
    staff_api_client, permission_manage_shipping, shipping_method
):
    # given
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_method_id,
        "ShippingMethodType",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        shipping_method,
        shipping_method_id,
    )


def test_add_private_metadata_for_shipping_zone(
    staff_api_client, permission_manage_shipping, shipping_zone
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_shipping,
        shipping_zone_id,
        "ShippingZone",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        shipping_zone,
        shipping_zone_id,
    )
