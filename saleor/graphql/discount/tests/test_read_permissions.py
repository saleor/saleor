"""READ_DISCOUNTS permission model (discount domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_DISCOUNTS sees the same reads as MANAGE_DISCOUNTS
  B. No write leak - READ_DISCOUNTS is rejected by MANAGE_DISCOUNTS mutations
  C. Regression    - MANAGE_DISCOUNTS behavior unchanged; no-perms still denied
  E. Metadata      - READ_DISCOUNTS unlocks private metadata reads (dynamic perm resolution)
  G. Grant-scope   - MANAGE_DISCOUNTS covers granting its READ_DISCOUNTS twin (appCreate)

The discount domain has no manual read gates: every read is gated through a
`PermissionsField(permissions=[MANAGE_DISCOUNTS])` (auto-widened at
`core/fields.py`) or private-metadata resolution. These tests lock the parity in.
"""

import graphene

from ....permission.enums import DiscountPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

PROMOTION_QUERY = """
    query ($id: ID!) {
        promotion(id: $id) {
            id
            name
        }
    }
"""

PROMOTION_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        promotion(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

PROMOTIONS_LIST_QUERY = """
    query {
        promotions(first: 20) {
            edges { node { id } }
        }
    }
"""

PROMOTION_DELETE_MUTATION = """
    mutation ($id: ID!) {
        promotionDelete(id: $id) {
            promotion { id }
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
# A. Parity - READ_DISCOUNTS sees the same reads as MANAGE_DISCOUNTS
# --------------------------------------------------------------------------- #


def test_read_discounts_reads_promotion(
    staff_api_client, catalogue_promotion, permission_read_discounts
):
    # given a staff user holding only READ_DISCOUNTS
    promotion = catalogue_promotion
    staff_api_client.user.user_permissions.add(permission_read_discounts)
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.pk)}

    # when reading the permission-gated promotion field
    response = staff_api_client.post_graphql(PROMOTION_QUERY, variables)

    # then the promotion is returned (parity with MANAGE_DISCOUNTS)
    content = get_graphql_content(response)
    assert content["data"]["promotion"]["name"] == promotion.name


def test_app_with_read_discounts_can_list_promotions(
    app_api_client, catalogue_promotion, permission_read_discounts
):
    # given an app holding READ_DISCOUNTS
    app_api_client.app.permissions.add(permission_read_discounts)

    # when listing promotions
    response = app_api_client.post_graphql(
        PROMOTIONS_LIST_QUERY, check_no_permissions=False
    )

    # then the promotion is listed (apps are a primary target audience)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["promotions"]["edges"]}
    assert graphene.Node.to_global_id("Promotion", catalogue_promotion.pk) in ids


# --------------------------------------------------------------------------- #
# B. No write leak - READ_DISCOUNTS is rejected by MANAGE_DISCOUNTS mutations
# --------------------------------------------------------------------------- #


def test_read_discounts_cannot_delete_promotion(
    staff_api_client, catalogue_promotion, permission_read_discounts
):
    # given a staff user holding only READ_DISCOUNTS
    from ....discount.models import Promotion

    promotion = catalogue_promotion
    staff_api_client.user.user_permissions.add(permission_read_discounts)
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.pk)}

    # when attempting a MANAGE_DISCOUNTS mutation
    response = staff_api_client.post_graphql(PROMOTION_DELETE_MUTATION, variables)

    # then it is denied and the promotion is unchanged
    assert_no_permission(response)
    assert Promotion.objects.filter(pk=promotion.pk).exists()


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_DISCOUNTS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_discounts_still_reads_promotion(
    staff_api_client, catalogue_promotion, permission_manage_discounts
):
    # given a staff user holding MANAGE_DISCOUNTS (baseline)
    promotion = catalogue_promotion
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.pk)}

    # when reading the promotion field
    response = staff_api_client.post_graphql(PROMOTION_QUERY, variables)

    # then the promotion is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["promotion"]["name"] == promotion.name


def test_no_perms_staff_cannot_read_promotion(staff_api_client, catalogue_promotion):
    # given a staff user with no relevant permissions
    variables = {"id": graphene.Node.to_global_id("Promotion", catalogue_promotion.pk)}

    # when reading the permission-gated promotion field
    response = staff_api_client.post_graphql(PROMOTION_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# E. Metadata - READ_DISCOUNTS unlocks private metadata reads
# --------------------------------------------------------------------------- #


def test_read_discounts_reads_promotion_private_metadata(
    staff_api_client, catalogue_promotion, permission_read_discounts
):
    # given a promotion with private metadata and a READ_DISCOUNTS-only staff user
    promotion = catalogue_promotion
    promotion.store_value_in_private_metadata({"secret": "value"})
    promotion.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_discounts)
    variables = {"id": graphene.Node.to_global_id("Promotion", promotion.pk)}

    # when reading the promotion's private metadata
    response = staff_api_client.post_graphql(PROMOTION_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["promotion"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_DISCOUNTS covers granting its READ_DISCOUNTS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_discounts_inferred_from_manage_discounts(
    staff_api_client, permission_manage_apps, permission_manage_discounts
):
    # given a staff user with MANAGE_APPS + MANAGE_DISCOUNTS and NO READ_DISCOUNTS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_discounts
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_DISCOUNTS.name],
    }

    # when creating an app that should hold READ_DISCOUNTS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_discounts - inferred from MANAGE_DISCOUNTS
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_DISCOUNTS.name}


def test_registry_maps_discount_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_DISCOUNTS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[DiscountPermissions.MANAGE_DISCOUNTS]
        == DiscountPermissions.READ_DISCOUNTS
    )
