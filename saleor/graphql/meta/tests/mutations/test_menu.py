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


def test_delete_private_metadata_for_menu(
    staff_api_client, permission_manage_menus, menu
):
    # given
    menu.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu.save(update_fields=["metadata"])
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        menu,
        menu_id,
    )


def test_delete_private_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item.store_value_in_private_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu_item.save(update_fields=["metadata"])
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_clear_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_without_private_metadata(
        response["data"]["deletePrivateMetadata"]["item"],
        menu_item,
        menu_item_id,
    )


def test_delete_public_metadata_for_menu(
    staff_api_client, permission_manage_menus, menu
):
    # given
    menu.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu.save(update_fields=["metadata"])
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        menu,
        menu_id,
    )


def test_delete_public_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item.store_value_in_metadata({PUBLIC_KEY: PUBLIC_VALUE})
    menu_item.save(update_fields=["metadata"])
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_clear_public_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_without_public_metadata(
        response["data"]["deleteMetadata"]["item"],
        menu_item,
        menu_item_id,
    )


def test_add_public_metadata_for_menu(staff_api_client, permission_manage_menus, menu):
    # given
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        menu,
        menu_id,
    )


def test_add_public_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_update_public_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_contains_proper_public_metadata(
        response["data"]["updateMetadata"]["item"],
        menu_item,
        menu_item_id,
    )


def test_add_private_metadata_for_menu(staff_api_client, permission_manage_menus, menu):
    # given
    menu_id = graphene.Node.to_global_id("Menu", menu.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_id,
        "Menu",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        menu,
        menu_id,
    )


def test_add_private_metadata_for_menu_item(
    staff_api_client, permission_manage_menus, menu_item
):
    # given
    menu_item_id = graphene.Node.to_global_id("MenuItem", menu_item.pk)

    # when
    response = execute_update_private_metadata_for_item(
        staff_api_client,
        permission_manage_menus,
        menu_item_id,
        "MenuItem",
    )

    # then
    assert item_contains_proper_private_metadata(
        response["data"]["updatePrivateMetadata"]["item"],
        menu_item,
        menu_item_id,
    )
