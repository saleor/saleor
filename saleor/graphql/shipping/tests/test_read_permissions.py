"""READ_SHIPPING permission model (shipping domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_SHIPPING sees the same reads as MANAGE_SHIPPING
  B. No write leak - READ_SHIPPING is rejected by MANAGE_SHIPPING mutations
  C. Regression    - MANAGE_SHIPPING behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_SHIPPING covers granting its READ_SHIPPING twin (appCreate)

The `shippingZones` query is gated through `PermissionsField(permissions=[MANAGE_SHIPPING])`
(auto-widened at `core/fields.py`). These tests lock the parity in via that query.
"""

import graphene

from ....permission.enums import ShippingPermissions
from ....shipping.models import ShippingZone
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

SHIPPING_ZONES_QUERY = """
    query {
        shippingZones(first: 10) {
            edges { node { id name } }
        }
    }
"""

SHIPPING_ZONE_CREATE_MUTATION = """
    mutation ($name: String!) {
        shippingZoneCreate(input: {name: $name}) {
            shippingZone { id }
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
# A. Parity - READ_SHIPPING sees the same reads as MANAGE_SHIPPING
# --------------------------------------------------------------------------- #


def test_read_shipping_reads_shipping_zones(
    staff_api_client, shipping_zone, permission_read_shipping
):
    # given a shipping zone and a staff user holding only READ_SHIPPING
    staff_api_client.user.user_permissions.add(permission_read_shipping)

    # when reading the permission-gated shipping zones list
    response = staff_api_client.post_graphql(SHIPPING_ZONES_QUERY)

    # then the zone is returned (parity with MANAGE_SHIPPING)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["shippingZones"]["edges"]}
    assert ids == {graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)}


# --------------------------------------------------------------------------- #
# B. No write leak - READ_SHIPPING is rejected by MANAGE_SHIPPING mutations
# --------------------------------------------------------------------------- #


def test_read_shipping_cannot_create_shipping_zone(
    staff_api_client, permission_read_shipping
):
    # given a staff user holding only READ_SHIPPING
    staff_api_client.user.user_permissions.add(permission_read_shipping)
    variables = {"name": "new zone"}

    # when attempting a MANAGE_SHIPPING mutation
    response = staff_api_client.post_graphql(SHIPPING_ZONE_CREATE_MUTATION, variables)

    # then it is denied and no zone is created
    assert_no_permission(response)
    assert ShippingZone.objects.filter(name="new zone").exists() is False


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_SHIPPING unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_shipping_still_reads_shipping_zones(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    # given a shipping zone and a staff user holding MANAGE_SHIPPING (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_shipping)

    # when reading the shipping zones list
    response = staff_api_client.post_graphql(SHIPPING_ZONES_QUERY)

    # then the zone is returned (no regression)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["shippingZones"]["edges"]}
    assert ids == {graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)}


def test_no_perms_staff_cannot_read_shipping_zones(staff_api_client, shipping_zone):
    # given a staff user with no relevant permissions

    # when reading the permission-gated shipping zones list
    response = staff_api_client.post_graphql(SHIPPING_ZONES_QUERY)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_SHIPPING covers granting its READ_SHIPPING twin
# --------------------------------------------------------------------------- #


def test_app_create_read_shipping_inferred_from_manage_shipping(
    staff_api_client, permission_manage_apps, permission_manage_shipping
):
    # given a staff user with MANAGE_APPS + MANAGE_SHIPPING and NO READ_SHIPPING
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_shipping
    )
    variables = {"name": "read app", "permissions": [PermissionEnum.READ_SHIPPING.name]}

    # when creating an app that should hold READ_SHIPPING
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_shipping - inferred from MANAGE_SHIPPING
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_SHIPPING.name}


def test_registry_maps_shipping_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_SHIPPING maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[ShippingPermissions.MANAGE_SHIPPING]
        == ShippingPermissions.READ_SHIPPING
    )
