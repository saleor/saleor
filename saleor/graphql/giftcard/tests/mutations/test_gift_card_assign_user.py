import graphene
from django.utils import timezone

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.utils import assign_gift_card_to_user
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Assign($id: ID!, $userId: ID!) {
        giftCardAssignUser(id: $id, userId: $userId) {
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


def _assign_event(gift_card_data):
    return next(
        event
        for event in gift_card_data["events"]
        if event["type"] == GiftCardEvents.ASSIGNED_TO_USER.upper()
    )


def _vars(gift_card, user):
    return {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "userId": graphene.Node.to_global_id("User", user.pk),
    }


def test_assign_user(
    staff_api_client,
    gift_card,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card, customer_user),
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).count() == 1

    assignment = _assign_event(data["giftCard"])["assignedTo"]
    assert assignment["oldAssignedTo"] is None
    assert assignment["oldAssignedToEmail"] is None
    assert assignment["currentAssignedTo"]["email"] == customer_user.email
    assert assignment["currentAssignedToEmail"] == customer_user.email


def test_reassign_records_previous(
    staff_api_client,
    gift_card,
    customer_user,
    staff_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    assign_gift_card_to_user(gift_card, staff_user)

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card, customer_user),
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    event = gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).last()
    assert event.parameters["previous_assigned_to_id"] == staff_user.id
    assert event.parameters["assigned_to_id"] == customer_user.id

    assignment = _assign_event(data["giftCard"])["assignedTo"]
    assert assignment["oldAssignedTo"]["email"] == staff_user.email
    assert assignment["oldAssignedToEmail"] == staff_user.email
    assert assignment["currentAssignedTo"]["email"] == customer_user.email
    assert assignment["currentAssignedToEmail"] == customer_user.email


def test_assigned_to_user_fields_require_manage_users(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given a requester with MANAGE_GIFT_CARD but not MANAGE_USERS

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card, customer_user),
        permissions=[permission_manage_gift_card],
    )

    # then the User sub-field is denied while the email sub-field still resolves
    content = get_graphql_content(response, ignore_errors=True)
    data = content["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    assignment = _assign_event(data["giftCard"])["assignedTo"]
    assert assignment["currentAssignedTo"] is None
    assert assignment["currentAssignedToEmail"] == customer_user.email
    assert any(
        error["message"] == "To access this path, you need one of the following "
        "permissions: MANAGE_USERS, MANAGE_STAFF, OWNER"
        for error in content["errors"]
    )


def test_assign_blocked_when_used(
    staff_api_client, gift_card_used, customer_user, permission_manage_gift_card
):
    # given
    gift_card_used.last_used_on = timezone.now()
    gift_card_used.save(update_fields=["last_used_on"])

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card_used, customer_user),
        permissions=[permission_manage_gift_card],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["code"] == GiftCardErrorCode.CANNOT_ASSIGN.name


def test_requires_permission(staff_api_client, gift_card, customer_user):
    # when
    response = staff_api_client.post_graphql(MUTATION, _vars(gift_card, customer_user))

    # then
    assert_no_permission(response)
    gift_card.refresh_from_db()
    assert gift_card.assigned_to is None
    assert gift_card.assigned_to_email is None


def test_empty_gift_card_id_is_rejected(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    variables = {
        "id": "",
        "userId": graphene.Node.to_global_id("User", customer_user.pk),
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == GiftCardErrorCode.NOT_FOUND.name


def test_empty_user_id_is_rejected(
    staff_api_client, gift_card, permission_manage_gift_card, permission_manage_users
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "userId": "",
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["field"] == "userId"
    assert data["errors"][0]["code"] == GiftCardErrorCode.NOT_FOUND.name
    gift_card.refresh_from_db()
    assert gift_card.assigned_to is None
