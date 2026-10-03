"""READ_GIFT_CARD permission model (gift card domain).

Seam under test: the GraphQL API (execute query/mutation as a principal, observe response).

Invariants:
  A. Parity        - READ_GIFT_CARD sees the same reads as MANAGE_GIFT_CARD
  B. No write leak - READ_GIFT_CARD is rejected by MANAGE_GIFT_CARD mutations
  C. Regression    - MANAGE_GIFT_CARD behavior unchanged; no-perms still denied
  E. Metadata      - READ_GIFT_CARD unlocks private metadata reads (dynamic perm resolution)
  G. Grant-scope   - MANAGE_GIFT_CARD covers granting its READ_GIFT_CARD twin (appCreate)

Parity is enforced through the `giftCard` list/detail field gate plus the manual
owner/permission gates widened via expand_read_permissions: `code`,
`createdByEmail`, and the `events` full-vs-order-subset filter.
"""

import graphene

from ....giftcard import GiftCardEvents
from ....giftcard.models import GiftCardEvent
from ....permission.enums import GiftcardPermissions
from ...core.enums import PermissionEnum
from ...tests.utils import assert_no_permission, get_graphql_content

GIFT_CARD_CODE_QUERY = """
    query ($id: ID!) {
        giftCard(id: $id) {
            id
            code
        }
    }
"""

GIFT_CARD_CREATED_BY_EMAIL_QUERY = """
    query ($id: ID!) {
        giftCard(id: $id) {
            id
            createdByEmail
        }
    }
"""

GIFT_CARD_EVENTS_QUERY = """
    query ($id: ID!) {
        giftCard(id: $id) {
            id
            events { type }
        }
    }
"""

GIFT_CARD_PRIVATE_META_QUERY = """
    query ($id: ID!) {
        giftCard(id: $id) {
            id
            privateMetadata { key value }
        }
    }
"""

GIFT_CARDS_LIST_QUERY = """
    query {
        giftCards(first: 20) {
            edges { node { id } }
        }
    }
"""

GIFT_CARD_DEACTIVATE_MUTATION = """
    mutation ($id: ID!) {
        giftCardDeactivate(id: $id) {
            giftCard { id isActive }
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
# A. Parity - READ_GIFT_CARD sees the same reads as MANAGE_GIFT_CARD
# --------------------------------------------------------------------------- #


def test_read_gift_card_reads_code(
    staff_api_client, gift_card, permission_read_gift_card
):
    # given a non-owner staff user holding only READ_GIFT_CARD
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    assert gift_card.used_by_id != staff_api_client.user.pk
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the owner/permission-gated code field
    response = staff_api_client.post_graphql(GIFT_CARD_CODE_QUERY, variables)

    # then the code is returned (parity with MANAGE_GIFT_CARD)
    content = get_graphql_content(response)
    assert content["data"]["giftCard"]["code"] == gift_card.code


def test_read_gift_card_reads_created_by_email_unobfuscated(
    staff_api_client, gift_card, permission_read_gift_card
):
    # given a non-owner staff user holding only READ_GIFT_CARD
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the permission-gated createdByEmail field
    response = staff_api_client.post_graphql(
        GIFT_CARD_CREATED_BY_EMAIL_QUERY, variables
    )

    # then the real (unobfuscated) email is returned (parity with MANAGE_GIFT_CARD)
    content = get_graphql_content(response)
    assert content["data"]["giftCard"]["createdByEmail"] == gift_card.created_by_email


def test_read_gift_card_reads_all_events(
    staff_api_client, gift_card, permission_read_gift_card
):
    # given a gift card with a staff-only (non-order) event
    event = GiftCardEvent.objects.create(
        gift_card=gift_card, type=GiftCardEvents.ISSUED
    )
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the events field
    response = staff_api_client.post_graphql(GIFT_CARD_EVENTS_QUERY, variables)

    # then the non-order event is visible (READ_GIFT_CARD bypasses the order subset)
    content = get_graphql_content(response)
    types = [e["type"] for e in content["data"]["giftCard"]["events"]]
    assert types == [event.type.upper()]


def test_app_with_read_gift_card_can_list_gift_cards(
    app_api_client, gift_card, permission_read_gift_card
):
    # given an app holding READ_GIFT_CARD
    app_api_client.app.permissions.add(permission_read_gift_card)

    # when listing gift cards
    response = app_api_client.post_graphql(
        GIFT_CARDS_LIST_QUERY, check_no_permissions=False
    )

    # then the gift card is listed (apps are a primary target audience)
    content = get_graphql_content(response)
    ids = {edge["node"]["id"] for edge in content["data"]["giftCards"]["edges"]}
    assert graphene.Node.to_global_id("GiftCard", gift_card.pk) in ids


# --------------------------------------------------------------------------- #
# B. No write leak - READ_GIFT_CARD is rejected by MANAGE_GIFT_CARD mutations
# --------------------------------------------------------------------------- #


def test_read_gift_card_cannot_deactivate(
    staff_api_client, gift_card, permission_read_gift_card
):
    # given an active gift card and a READ_GIFT_CARD-only staff user
    assert gift_card.is_active is True
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when attempting a MANAGE_GIFT_CARD mutation
    response = staff_api_client.post_graphql(GIFT_CARD_DEACTIVATE_MUTATION, variables)

    # then it is denied and the gift card stays active
    assert_no_permission(response)
    gift_card.refresh_from_db(fields=["is_active"])
    assert gift_card.is_active is True


# --------------------------------------------------------------------------- #
# C. Regression - MANAGE_GIFT_CARD unchanged; no-perms denied
# --------------------------------------------------------------------------- #


def test_manage_gift_card_still_reads_code(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given a staff user holding MANAGE_GIFT_CARD (baseline)
    staff_api_client.user.user_permissions.add(permission_manage_gift_card)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the code field
    response = staff_api_client.post_graphql(GIFT_CARD_CODE_QUERY, variables)

    # then the code is returned (no regression)
    content = get_graphql_content(response)
    assert content["data"]["giftCard"]["code"] == gift_card.code


def test_no_perms_staff_cannot_read_gift_card(staff_api_client, gift_card):
    # given a staff user with no relevant permissions
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the permission-gated giftCard field
    response = staff_api_client.post_graphql(GIFT_CARD_CODE_QUERY, variables)

    # then it is denied - adding the READ twin did not widen unprivileged access
    assert_no_permission(response)


# --------------------------------------------------------------------------- #
# E. Metadata - READ_GIFT_CARD unlocks private metadata reads
# --------------------------------------------------------------------------- #


def test_read_gift_card_reads_private_metadata(
    staff_api_client, gift_card, permission_read_gift_card
):
    # given a gift card with private metadata and a READ_GIFT_CARD-only staff user
    gift_card.store_value_in_private_metadata({"secret": "value"})
    gift_card.save(update_fields=["private_metadata"])
    staff_api_client.user.user_permissions.add(permission_read_gift_card)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when reading the gift card's private metadata
    response = staff_api_client.post_graphql(GIFT_CARD_PRIVATE_META_QUERY, variables)

    # then the private metadata is returned
    content = get_graphql_content(response)
    metadata = {
        item["key"]: item["value"]
        for item in content["data"]["giftCard"]["privateMetadata"]
    }
    assert metadata["secret"] == "value"


# --------------------------------------------------------------------------- #
# G. Grant-scope - MANAGE_GIFT_CARD covers granting its READ_GIFT_CARD twin
# --------------------------------------------------------------------------- #


def test_app_create_read_gift_card_inferred_from_manage_gift_card(
    staff_api_client, permission_manage_apps, permission_manage_gift_card
):
    # given a staff user with MANAGE_APPS + MANAGE_GIFT_CARD and NO READ_GIFT_CARD
    staff_api_client.user.user_permissions.add(
        permission_manage_apps, permission_manage_gift_card
    )
    variables = {
        "name": "read app",
        "permissions": [PermissionEnum.READ_GIFT_CARD.name],
    }

    # when creating an app that should hold READ_GIFT_CARD
    response = staff_api_client.post_graphql(APP_CREATE_MUTATION, variables)

    # then the app is created holding read_gift_card - inferred from MANAGE_GIFT_CARD
    content = get_graphql_content(response)
    data = content["data"]["appCreate"]
    assert data["errors"] == []
    codes = {perm["code"] for perm in data["app"]["permissions"]}
    assert codes == {PermissionEnum.READ_GIFT_CARD.name}


def test_registry_maps_gift_card_twin():
    # given the registry entries
    from ....permission.read_permissions import MANAGE_TO_READ_PERMISSION_MAP

    # then MANAGE_GIFT_CARD maps to its READ twin
    assert (
        MANAGE_TO_READ_PERMISSION_MAP[GiftcardPermissions.MANAGE_GIFT_CARD]
        == GiftcardPermissions.READ_GIFT_CARD
    )
