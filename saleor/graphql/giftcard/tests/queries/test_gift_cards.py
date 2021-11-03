import graphene

from ....tests.utils import get_graphql_content

QUERY_GIFT_CARDS = """
    query giftCards{
        giftCards(first: 10) {
            edges {
                node {
                    id
                    last4CodeChars
                }
            }
            totalCount
        }
    }
"""


def test_query_gift_cards_by_staff(
    staff_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_created_by_staff_id = graphene.Node.to_global_id(
        "GiftCard", gift_card_created_by_staff.pk
    )

    # when
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 2
    assert data[0]["node"]["id"] == gift_card_created_by_staff_id
    assert data[0]["node"]["last4CodeChars"] == gift_card_created_by_staff.display_code
    assert data[1]["node"]["id"] == gift_card_id
    assert data[1]["node"]["last4CodeChars"] == gift_card.display_code


def test_query_gift_cards_by_app(
    app_api_client, gift_card, gift_card_created_by_staff, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    gift_card_created_by_staff_id = graphene.Node.to_global_id(
        "GiftCard", gift_card_created_by_staff.pk
    )

    # when
    response = app_api_client.post_graphql(
        query, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 2
    assert data[0]["node"]["id"] == gift_card_created_by_staff_id
    assert data[0]["node"]["last4CodeChars"] == gift_card_created_by_staff.display_code
    assert data[1]["node"]["id"] == gift_card_id
    assert data[1]["node"]["last4CodeChars"] == gift_card.display_code


def test_query_own_gift_cards(
    user_api_client, gift_card_used, gift_card_created_by_staff
):
    query = """
        query giftCards{
            me {
                giftCards(first: 10) {
                    edges {
                        node {
                            id
                            last4CodeChars
                            code
                        }
                    }
                    totalCount
                }
            }
        }
    """
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)
    response = user_api_client.post_graphql(query)
    content = get_graphql_content(response)
    data = content["data"]["me"]["giftCards"]
    assert data["edges"][0]["node"]["id"] == gift_card_id
    assert data["edges"][0]["node"]["last4CodeChars"] == gift_card_used.display_code
    assert data["edges"][0]["node"]["code"] == gift_card_used.code
    assert data["totalCount"] == 1
