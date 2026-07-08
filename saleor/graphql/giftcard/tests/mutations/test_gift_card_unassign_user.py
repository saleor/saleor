import graphene

from .....giftcard import GiftCardEvents
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
    from .....giftcard.utils import assign_gift_card_to_user

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
    from .....giftcard.utils import assign_gift_card_to_user

    assign_gift_card_to_user(gift_card, customer_user)

    # when
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}
    response = staff_api_client.post_graphql(MUTATION, variables)

    # then
    assert_no_permission(response)
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
