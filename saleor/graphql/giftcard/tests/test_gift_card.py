import graphene

from ...tests.utils import assert_no_permission, get_graphql_content

DEACTIVATE_GIFT_CARD_MUTATION = """
mutation giftCardDeactivate($id: ID!) {
    giftCardDeactivate(id: $id) {
        errors {
            field
            message
        }
        giftCard {
            isActive
        }
    }
}
"""


def test_deactivate_gift_card(staff_api_client, gift_card, permission_manage_gift_card):
    assert gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        DEACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardDeactivate"]["giftCard"]
    assert not data["isActive"]


def test_deactivate_gift_card_without_premissions(staff_api_client, gift_card):
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(DEACTIVATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


def test_deactivate_gift_card_inactive_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card
):
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        DEACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardDeactivate"]["giftCard"]
    assert not data["isActive"]


ACTIVATE_GIFT_CARD_MUTATION = """
mutation giftCardActivate($id: ID!) {
    giftCardActivate(id: $id) {
        errors {
            field
            message
        }
        giftCard {
            isActive
        }
    }
}
"""


def test_activate_gift_card(staff_api_client, gift_card, permission_manage_gift_card):
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])
    assert not gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]


def test_activate_gift_card_without_premissions(staff_api_client, gift_card):
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(ACTIVATE_GIFT_CARD_MUTATION, variables)
    assert_no_permission(response)


def test_activate_gift_card_active_gift_card(
    staff_api_client, gift_card, permission_manage_gift_card
):
    assert gift_card.is_active
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.id)}
    response = staff_api_client.post_graphql(
        ACTIVATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardActivate"]["giftCard"]
    assert data["isActive"]
