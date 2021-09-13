import graphene
import pytest

from ....tests.utils import assert_no_permission, get_graphql_content

DELETE_GIFT_CARD_MUTATION = """
    mutation DeleteGiftCard($id: ID!) {
        giftCardDelete(id: $id) {
            giftCard {
                id
            }
        }
    }
"""


def test_delete_gift_card_by_staff(
    staff_api_client, gift_card, permission_manage_gift_card
):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_GIFT_CARD_MUTATION,
        {"id": id},
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardDelete"]["giftCard"]

    assert data["id"] == id
    with pytest.raises(gift_card._meta.model.DoesNotExist):
        gift_card.refresh_from_db()


def test_delete_gift_card_by_staff_no_permission(staff_api_client, gift_card):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = staff_api_client.post_graphql(DELETE_GIFT_CARD_MUTATION, {"id": id})

    # then
    assert_no_permission(response)


def test_delete_gift_card_by_app(
    app_api_client, gift_card, permission_manage_gift_card
):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = app_api_client.post_graphql(
        DELETE_GIFT_CARD_MUTATION,
        {"id": id},
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardDelete"]["giftCard"]

    assert data["id"] == id
    with pytest.raises(gift_card._meta.model.DoesNotExist):
        gift_card.refresh_from_db()


def test_delete_gift_card_by_customer(app_api_client, gift_card):
    # given
    id = graphene.Node.to_global_id("GiftCard", gift_card.pk)

    # when
    response = app_api_client.post_graphql(DELETE_GIFT_CARD_MUTATION, {"id": id})

    # then
    assert_no_permission(response)
