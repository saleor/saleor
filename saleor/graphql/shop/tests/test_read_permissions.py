"""READ_SETTINGS permission model (shop/site domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_SETTINGS sees the same reads as MANAGE_SETTINGS
  B. No write leak - READ_SETTINGS is rejected by MANAGE_SETTINGS mutations
  C. Regression    - MANAGE_SETTINGS behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_SETTINGS covers granting its READ_SETTINGS twin (appCreate)

The MANAGE_SETTINGS reads on the `Shop` type are gated through
`PermissionsField(permissions=[MANAGE_SETTINGS])` (auto-widened at `core/fields.py`).
These tests lock the parity in via `limitQuantityPerCheckout`.
"""

from ....permission.enums import SitePermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

SHOP_LIMIT_QUERY = """
    query {
        shop {
            limitQuantityPerCheckout
        }
    }
"""

SHOP_SETTINGS_UPDATE_MUTATION = """
    mutation ($input: ShopSettingsInput!) {
        shopSettingsUpdate(input: $input) {
            shop { limitQuantityPerCheckout }
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


# --------------------------------------------------------------------------- #
# A. Parity - READ_SETTINGS sees the same reads as MANAGE_SETTINGS
# --------------------------------------------------------------------------- #


def test_read_settings_reads_limit_quantity_per_checkout(
    staff_api_client, site_settings, permission_read_settings
):
    # given a configured limit and a staff user holding only READ_SETTINGS
    limit = 7
    site_settings.limit_quantity_per_checkout = limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    staff_api_client.user.user_permissions.add(permission_read_settings)

    # when reading the permission-gated shop field
    response = staff_api_client.post_graphql(SHOP_LIMIT_QUERY)

    # then the value is returned (parity with MANAGE_SETTINGS)
    content = get_graphql_content(response)
    assert content["data"]["shop"]["limitQuantityPerCheckout"] == limit


# --------------------------------------------------------------------------- #
# B. No write leak - READ_SETTINGS is rejected by MANAGE_SETTINGS mutations
# --------------------------------------------------------------------------- #


def test_read_settings_cannot_update_shop_settings(
    staff_api_client, site_settings, permission_read_settings
):
    # given a configured limit and a staff user holding only READ_SETTINGS
    original_limit = 7
    site_settings.limit_quantity_per_checkout = original_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    staff_api_client.user.user_permissions.add(permission_read_settings)
    variables = {"input": {"limitQuantityPerCheckout": 99}}

    # when attempting a MANAGE_SETTINGS mutation
    response = staff_api_client.post_graphql(SHOP_SETTINGS_UPDATE_MUTATION, variables)

    # then it is denied and the setting is unchanged
    assert_no_permission(response)
    site_settings.refresh_from_db(fields=["limit_quantity_per_checkout"])
    assert site_settings.limit_quantity_per_checkout == original_limit


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_SETTINGS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_settings_still_reads_limit_quantity_per_checkout(
    staff_api_client, site_settings, permission_manage_settings
):
    # given a configured limit and a staff user holding MANAGE_SETTINGS (baseline)
    limit = 7
    site_settings.limit_quantity_per_checkout = limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    staff_api_client.user.user_permissions.add(permission_manage_settings)

    # when reading the shop field
    response = staff_api_client.post_graphql(SHOP_LIMIT_QUERY)

    # then the value is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["shop"]["limitQuantityPerCheckout"] == limit


def test_no_perms_staff_cannot_read_limit_quantity_per_checkout(
    staff_api_client, site_settings
):
    # given a staff user with no relevant permissions
    site_settings.limit_quantity_per_checkout = 7
    site_settings.save(update_fields=["limit_quantity_per_checkout"])

    # when reading the permission-gated shop field
    response = staff_api_client.post_graphql(SHOP_LIMIT_QUERY)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_SETTINGS covers granting its READ_SETTINGS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_settings_inferred_from_manage_settings(
    staff_api_client, permission_manage_apps, permission_manage_settings
):
    # given a staff user with MANAGE_APPS + MANAGE_SETTINGS and NO READ_SETTINGS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_settings
    )
    variables = {"name": "read app", "permissions": [PermissionEnum.READ_SETTINGS.name]}

    # when creating an app that should hold READ_SETTINGS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_settings - inferred from MANAGE_SETTINGS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_SETTINGS.name}


def test_registry_maps_settings_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_SETTINGS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[SitePermissions.MANAGE_SETTINGS]
        == SitePermissions.READ_SETTINGS
    )
