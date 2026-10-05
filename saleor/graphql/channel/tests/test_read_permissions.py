"""READ_CHANNELS permission model (channel domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_CHANNELS sees the same reads as MANAGE_CHANNELS
  B. No write leak - READ_CHANNELS is rejected by MANAGE_CHANNELS mutations
  C. Regression    - MANAGE_CHANNELS behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_CHANNELS covers granting its READ_CHANNELS twin (appCreate)

The MANAGE_CHANNELS reads on the `Channel` type are gated through
`PermissionsField(permissions=[MANAGE_CHANNELS])` (auto-widened at `core/fields.py`).
These tests lock the parity in via `Channel.hasOrders`.
"""

import graphene

from ....permission.enums import ChannelPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

CHANNEL_HAS_ORDERS_QUERY = """
    query ($id: ID!) {
        channel(id: $id) {
            hasOrders
        }
    }
"""

CHANNEL_DEACTIVATE_MUTATION = """
    mutation ($id: ID!) {
        channelDeactivate(id: $id) {
            channel { isActive }
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
# A. Parity - READ_CHANNELS sees the same reads as MANAGE_CHANNELS
# --------------------------------------------------------------------------- #


def test_read_channels_reads_has_orders(
    staff_api_client, channel_USD, permission_read_channels
):
    # given a staff user holding only READ_CHANNELS
    staff_api_client.user.user_permissions.add(permission_read_channels)
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when reading the permission-gated channel field
    response = staff_api_client.post_graphql(CHANNEL_HAS_ORDERS_QUERY, variables)

    # then the value is returned (parity with MANAGE_CHANNELS)
    content = get_graphql_content(response)
    assert content["data"]["channel"]["hasOrders"] is False


# --------------------------------------------------------------------------- #
# B. No write leak - READ_CHANNELS is rejected by MANAGE_CHANNELS mutations
# --------------------------------------------------------------------------- #


def test_read_channels_cannot_deactivate_channel(
    staff_api_client, channel_USD, permission_read_channels
):
    # given an active channel and a staff user holding only READ_CHANNELS
    assert channel_USD.is_active is True
    staff_api_client.user.user_permissions.add(permission_read_channels)
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when attempting a MANAGE_CHANNELS mutation
    response = staff_api_client.post_graphql(CHANNEL_DEACTIVATE_MUTATION, variables)

    # then it is denied and the channel is unchanged
    assert_no_permission(response)
    channel_USD.refresh_from_db(fields=["is_active"])
    assert channel_USD.is_active is True


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_CHANNELS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_channels_still_reads_has_orders(
    staff_api_client, channel_USD, permission_manage_channels
):
    # given a staff user holding MANAGE_CHANNELS (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_channels)
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when reading the channel field
    response = staff_api_client.post_graphql(CHANNEL_HAS_ORDERS_QUERY, variables)

    # then the value is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["channel"]["hasOrders"] is False


def test_no_perms_staff_cannot_read_has_orders(staff_api_client, channel_USD):
    # given a staff user with no relevant permissions
    variables = {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)}

    # when reading the permission-gated channel field
    response = staff_api_client.post_graphql(CHANNEL_HAS_ORDERS_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_CHANNELS covers granting its READ_CHANNELS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_channels_inferred_from_manage_channels(
    staff_api_client, permission_manage_apps, permission_manage_channels
):
    # given a staff user with MANAGE_APPS + MANAGE_CHANNELS and NO READ_CHANNELS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_channels
    )
    variables = {"name": "read app", "permissions": [PermissionEnum.READ_CHANNELS.name]}

    # when creating an app that should hold READ_CHANNELS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_channels - inferred from MANAGE_CHANNELS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_CHANNELS.name}


def test_registry_maps_channels_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_CHANNELS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[ChannelPermissions.MANAGE_CHANNELS]
        == ChannelPermissions.READ_CHANNELS
    )
