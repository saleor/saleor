"""READ_MENUS permission model (menu domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_MENUS sees the same reads as MANAGE_MENUS
  B. No write leak - READ_MENUS is rejected by MANAGE_MENUS mutations
  C. Regression    - MANAGE_MENUS behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_MENUS covers granting its READ_MENUS twin (appCreate)

Menu list/detail reads are public; the only MANAGE_MENUS-gated read surface is the
private metadata, gated through the private-metadata chokepoint (auto-widened at
`meta/resolvers.py`). These tests lock the parity in via `Menu.privateMetadata`.
"""

import graphene

from ....menu.models import Menu
from ....permission.enums import MenuPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

MENU_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        menu(id: $id) {
            privateMetadata { key value }
        }
    }
"""

MENU_CREATE_MUTATION = """
    mutation ($name: String!) {
        menuCreate(input: {name: $name}) {
            menu { id }
            errors { field code }
        }
    }
"""

APP_CREATE_MUTATION = """
    mutation AppCreate($name: String, $permissions: [PermissionEnum!]) {
        appCreate(input: {name: $name, permissions: $permissions}) {
            app { permissions { code } }
            errors { field code permissions }
        }
    }
"""

META_KEY = "secret"
META_VALUE = "value"


# --------------------------------------------------------------------------- #
# A. Parity - READ_MENUS sees the same reads as MANAGE_MENUS
# --------------------------------------------------------------------------- #


def test_read_menus_reads_private_metadata(
    staff_api_client, menu, permission_read_menus
):
    # given a menu with private metadata and a staff user holding only READ_MENUS
    menu.store_value_in_private_metadata({META_KEY: META_VALUE})
    menu.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_menus)
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk)}

    # when reading the permission-gated private metadata
    response = staff_api_client.post_graphql(MENU_PRIVATE_META_QUERY, variables)

    # then the value is returned (parity with MANAGE_MENUS)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["privateMetadata"] == [
        {"key": META_KEY, "value": META_VALUE}
    ]


# --------------------------------------------------------------------------- #
# B. No write leak - READ_MENUS is rejected by MANAGE_MENUS mutations
# --------------------------------------------------------------------------- #


def test_read_menus_cannot_create_menu(staff_api_client, permission_read_menus):
    # given a staff user holding only READ_MENUS
    staff_api_client.user.user_permissions.add(permission_read_menus)
    variables = {"name": "new menu"}

    # when attempting a MANAGE_MENUS mutation
    response = staff_api_client.post_graphql(MENU_CREATE_MUTATION, variables)

    # then it is denied and no menu is created
    assert_no_permission(response)
    assert Menu.objects.filter(name="new menu").exists() is False


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_MENUS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_menus_still_reads_private_metadata(
    staff_api_client, menu, permission_manage_menus
):
    # given a menu with private metadata and a staff user holding MANAGE_MENUS
    menu.store_value_in_private_metadata({META_KEY: META_VALUE})
    menu.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_manage_menus)
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk)}

    # when reading the private metadata
    response = staff_api_client.post_graphql(MENU_PRIVATE_META_QUERY, variables)

    # then the value is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["menu"]["privateMetadata"] == [
        {"key": META_KEY, "value": META_VALUE}
    ]


def test_no_perms_staff_cannot_read_private_metadata(staff_api_client, menu):
    # given a menu with private metadata and a staff user with no relevant permissions
    menu.store_value_in_private_metadata({META_KEY: META_VALUE})
    menu.save(update_fields=["private_metadata"])
    variables = {"id": graphene.Node.to_global_id("Menu", menu.pk)}

    # when reading the permission-gated private metadata
    response = staff_api_client.post_graphql(MENU_PRIVATE_META_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_MENUS covers granting its READ_MENUS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_menus_inferred_from_manage_menus(
    staff_api_client, permission_manage_apps, permission_manage_menus
):
    # given a staff user with MANAGE_APPS + MANAGE_MENUS and NO READ_MENUS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_menus
    )
    variables = {"name": "read app", "permissions": [PermissionEnum.READ_MENUS.name]}

    # when creating an app that should hold READ_MENUS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_menus - inferred from MANAGE_MENUS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_MENUS.name}


def test_registry_maps_menus_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_MENUS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[MenuPermissions.MANAGE_MENUS]
        == MenuPermissions.READ_MENUS
    )
