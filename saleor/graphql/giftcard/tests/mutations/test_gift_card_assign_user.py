import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Assign($id: ID!, $userId: ID!) {
        giftCardAssignUser(id: $id, userId: $userId) {
            giftCard { id }
            errors { field code message }
        }
    }
"""


def _vars(gift_card, user):
    return {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "userId": graphene.Node.to_global_id("User", user.pk),
    }


def test_assign_user(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card, customer_user),
        permissions=[permission_manage_gift_card],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).count() == 1


def test_reassign_records_previous(
    staff_api_client, gift_card, customer_user, staff_user, permission_manage_gift_card
):
    # given
    from .....giftcard.utils import assign_gift_card_to_user

    assign_gift_card_to_user(gift_card, staff_user)

    # when
    response = staff_api_client.post_graphql(
        MUTATION,
        _vars(gift_card, customer_user),
        permissions=[permission_manage_gift_card],
    )

    # then
    data = get_graphql_content(response)["data"]["giftCardAssignUser"]
    assert data["errors"] == []
    event = gift_card.events.filter(type=GiftCardEvents.ASSIGNED_TO_USER).last()
    assert event.parameters["previous_assigned_to_id"] == staff_user.id
    assert event.parameters["assigned_to_id"] == customer_user.id


def test_assign_blocked_when_used(
    staff_api_client, gift_card_used, customer_user, permission_manage_gift_card
):
    # given
    from django.utils import timezone

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
