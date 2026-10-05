"""READ_CHECKOUTS permission model (checkout domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_CHECKOUTS sees the same reads as MANAGE_CHECKOUTS
  B. No write leak - READ_CHECKOUTS is rejected by MANAGE_CHECKOUTS mutations
  C. Regression    - MANAGE_CHECKOUTS behavior unchanged; no-perms still denied
  G. Grant-scope   - MANAGE_CHECKOUTS covers granting its READ_CHECKOUTS twin (appCreate)

Beyond the auto-widened `checkouts` list (`FilterConnectionField`), the checkout
domain has two MANUAL read gates that must widen explicitly:
  - `Checkout.transactions` (`@one_of_permissions_required`, which does NOT expand)
  - the single-`checkout` lookup for an inactive channel (`resolve_checkout`)
These tests exercise both widened gates directly.
"""

import graphene

from ....permission.enums import CheckoutPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

CHECKOUTS_LIST_QUERY = """
    query {
        checkouts(first: 20) {
            edges { node { id } }
        }
    }
"""

CHECKOUT_TRANSACTIONS_QUERY = """
    query ($id: ID!) {
        checkout(id: $id) {
            id
            transactions { id }
        }
    }
"""

CHECKOUT_QUERY = """
    query ($id: ID!) {
        checkout(id: $id) { id }
    }
"""

CHECKOUT_DELETE_MUTATION = """
    mutation ($id: ID!) {
        checkoutDelete(id: $id) {
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
# A. Parity - READ_CHECKOUTS sees the same reads as MANAGE_CHECKOUTS
# --------------------------------------------------------------------------- #


def test_read_checkouts_lists_checkouts(
    staff_api_client, checkout, permission_read_checkouts
):
    # given a checkout and a staff user holding only READ_CHECKOUTS
    staff_api_client.user.user_permissions.add(permission_read_checkouts)

    # when listing checkouts
    response = staff_api_client.post_graphql(CHECKOUTS_LIST_QUERY)

    # then the checkout is listed (parity with MANAGE_CHECKOUTS)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["checkouts"]["edges"]}
    assert graphene.Node.to_global_id("Checkout", checkout.pk) in ids


def test_read_checkouts_reads_checkout_transactions(
    staff_api_client, checkout, transaction_item_generator, permission_read_checkouts
):
    # given a checkout with a transaction and a READ_CHECKOUTS-only staff user
    transaction = transaction_item_generator(checkout_id=checkout.pk)
    staff_api_client.user.user_permissions.add(permission_read_checkouts)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when reading the `@one_of_permissions_required`-gated transactions field
    response = staff_api_client.post_graphql(CHECKOUT_TRANSACTIONS_QUERY, variables)

    # then the transaction is returned (widened manual gate)
    content = get_graphql_content(response)
    ids = {tx["id"] for tx in content["data"]["checkout"]["transactions"]}
    assert ids == {graphene.Node.to_global_id("TransactionItem", transaction.token)}


def test_read_checkouts_reads_checkout_in_inactive_channel(
    staff_api_client, checkout, channel_USD, permission_read_checkouts
):
    # given a checkout whose channel is inactive and a READ_CHECKOUTS-only staff user
    channel_USD.is_active = False
    channel_USD.save(update_fields=["is_active"])
    staff_api_client.user.user_permissions.add(permission_read_checkouts)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when reading the single checkout (resolve_checkout inactive-channel gate)
    response = staff_api_client.post_graphql(CHECKOUT_QUERY, variables)

    # then the checkout is returned (widened manual gate)
    content = get_graphql_content(response)
    assert content["data"]["checkout"]["id"] == graphene.Node.to_global_id(
        "Checkout", checkout.pk
    )


# --------------------------------------------------------------------------- #
# B. No write leak - READ_CHECKOUTS is rejected by MANAGE_CHECKOUTS mutations
# --------------------------------------------------------------------------- #


def test_read_checkouts_cannot_delete_checkout(
    staff_api_client, checkout, permission_read_checkouts
):
    # given a staff user holding only READ_CHECKOUTS
    from ....checkout.models import Checkout

    staff_api_client.user.user_permissions.add(permission_read_checkouts)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when attempting a MANAGE_CHECKOUTS mutation
    response = staff_api_client.post_graphql(CHECKOUT_DELETE_MUTATION, variables)

    # then it is denied and the checkout is unchanged
    assert_no_permission(response)
    assert Checkout.objects.filter(pk=checkout.pk).exists()


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_CHECKOUTS unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_checkouts_still_reads_checkout_transactions(
    staff_api_client, checkout, transaction_item_generator, permission_manage_checkouts
):
    # given a checkout with a transaction and a MANAGE_CHECKOUTS staff user (baseline)
    transaction = transaction_item_generator(checkout_id=checkout.pk)
    staff_api_client.user.user_permissions.add(permission_manage_checkouts)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when reading the transactions field
    response = staff_api_client.post_graphql(CHECKOUT_TRANSACTIONS_QUERY, variables)

    # then the transaction is returned (no regression)
    content = get_graphql_content(response)
    ids = {tx["id"] for tx in content["data"]["checkout"]["transactions"]}
    assert ids == {graphene.Node.to_global_id("TransactionItem", transaction.token)}


def test_no_perms_staff_cannot_read_checkout_transactions(
    staff_api_client, checkout, transaction_item_generator
):
    # given a checkout with a transaction and a staff user with no relevant perms
    transaction_item_generator(checkout_id=checkout.pk)
    variables = {"id": graphene.Node.to_global_id("Checkout", checkout.pk)}

    # when reading the transactions field
    response = staff_api_client.post_graphql(CHECKOUT_TRANSACTIONS_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_CHECKOUTS covers granting its READ_CHECKOUTS twin
# --------------------------------------------------------------------------- #


def test_app_create_read_checkouts_inferred_from_manage_checkouts(
    staff_api_client, permission_manage_apps, permission_manage_checkouts
):
    # given a staff user with MANAGE_APPS + MANAGE_CHECKOUTS and NO READ_CHECKOUTS
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_checkouts
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_CHECKOUTS.name],
    }

    # when creating an app that should hold READ_CHECKOUTS
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_checkouts - inferred from MANAGE
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_CHECKOUTS.name}


def test_registry_maps_checkouts_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_CHECKOUTS maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[CheckoutPermissions.MANAGE_CHECKOUTS]
        == CheckoutPermissions.READ_CHECKOUTS
    )
