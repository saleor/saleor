import graphene

from .....giftcard import GiftCardEvents
from ....tests.utils import assert_no_permission, get_graphql_content

MUTATION = """
    mutation Unassign($id: ID!) {
        giftCardUnassignUser(id: $id) {
            giftCard { id }
            errors { field code message }
        }
    }
"""


def test_unassign_clears_fields(
    staff_api_client, gift_card, customer_user, permission_manage_gift_card
):
    # given
    from .....giftcard.utils import assign_gift_card_to_user

    assign_gift_card_to_user(gift_card, customer_user)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_gift_card]
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


def test_requires_permission(staff_api_client, gift_card):
    # when
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}
    response = staff_api_client.post_graphql(MUTATION, variables)

    # then
    assert_no_permission(response)
