import graphene
import pytest

from ....tests.utils import get_graphql_content

QUERY_GIFT_CARDS = """
    query giftCards($filter: GiftCardFilterInput){
        giftCards(first: 10, filter: $filter) {
            edges {
                node {
                    id
                    displayCode
                }
            }
            totalCount
        }
    }
"""


def test_query_gift_cards(
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
    assert data[0]["node"]["displayCode"] == gift_card_created_by_staff.display_code
    assert data[1]["node"]["id"] == gift_card_id
    assert data[1]["node"]["displayCode"] == gift_card.display_code


@pytest.mark.parametrize(
    "filter_value, expected_gift_card_indexes",
    [
        ("test-tag", [0]),
        ("another-tag", [1, 2]),
        ("tag", [0, 1, 2, 3]),
        ("not existing", []),
    ],
)
def test_query_filter_gift_cards(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_period,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_cards = [
        gift_card,
        gift_card_expiry_period,
        gift_card_expiry_date,
        gift_card_used,
    ]
    variables = {"filter": {"tag": filter_value}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == len(expected_gift_card_indexes)
    assert {card["node"]["id"] for card in data} == {
        graphene.Node.to_global_id("GiftCard", gift_cards[i].pk)
        for i in expected_gift_card_indexes
    }


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
                            displayCode
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
    assert data["edges"][0]["node"]["displayCode"] == gift_card_used.display_code
    assert data["edges"][0]["node"]["code"] == gift_card_used.code
    assert data["totalCount"] == 1
