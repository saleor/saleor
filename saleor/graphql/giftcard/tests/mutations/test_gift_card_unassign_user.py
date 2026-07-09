import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.utils import assign_gift_card_to_user
from .....permission.enums import AccountPermissions
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Unassign($id: ID!) {
        giftCardUnassignUser(id: $id) {
            giftCard {
                id
                events {
                    type
                    assignedTo {
                        oldAssignedTo { email }
                        currentAssignedTo { email }
                        oldAssignedToEmail
                        currentAssignedToEmail
                    }
                }
            }
            errors { field code message }
        }
    }
"""


def _unassign_event(gift_card_data):
    return next(
        event
        for event in gift_card_data["events"]
        if event["type"] == GiftCardEvents.UNASSIGNED_FROM_USER.upper()
    )


def test_unassign_clears_fields(
    staff_api_client,
    gift_card,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    assign_gift_card_to_user(gift_card, customer_user)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardUnassignUser"]
    assert data["errors"] == []
    gift_card.refresh_from_db()
    assert gift_card.assigned_to is None
    assert gift_card.assigned_to_email is None
    assert (
        gift_card.events.filter(type=GiftCardEvents.UNASSIGNED_FROM_USER).count() == 1
    )

    assignment = _unassign_event(data["giftCard"])["assignedTo"]
    assert assignment["oldAssignedTo"]["email"] == customer_user.email
    assert assignment["oldAssignedToEmail"] == customer_user.email
    assert assignment["currentAssignedTo"] is None
    assert assignment["currentAssignedToEmail"] is None


def test_requires_permission(staff_api_client, gift_card, customer_user):
    # given
    assign_gift_card_to_user(gift_card, customer_user)

    # when
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}
    response = staff_api_client.post_graphql(MUTATION, variables)

    # then
    assert_no_permission(response)
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email


def test_assigned_to_user_fields_require_manage_users(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given a requester with MANAGE_GIFT_CARD but not MANAGE_USERS
    assign_gift_card_to_user(gift_card, customer_user)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
    )

    # then the event User sub-field is denied while the email sub-field resolves
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["giftCardUnassignUser"]
    assert data["errors"] == []
    assignment = _unassign_event(data["giftCard"])["assignedTo"]
    assert assignment["oldAssignedTo"] is None
    assert assignment["oldAssignedToEmail"] == customer_user.email
    assert any(
        AccountPermissions.MANAGE_USERS.name in error["message"]
        for error in content["errors"]
    )


def test_empty_id_is_rejected(
    staff_api_client, permission_manage_gift_card, permission_manage_users
):
    # given
    variables = {"id": ""}

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardUnassignUser"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == GiftCardErrorCode.NOT_FOUND.name
