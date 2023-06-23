import pytest

from ....tests.utils import get_graphql_content

QUERY_GIFT_CARDS = """
    query giftCards(
        $sortBy: GiftCardSortingInput,
        $filter: GiftCardFilterInput,
        $search: String,
    ){
        giftCards(first: 10, filter: $filter, sortBy: $sortBy, search: $search) {
            edges {
                node {
                    id
                    code
                }
            }
            totalCount
        }
    }
"""


@pytest.mark.parametrize("search,indexes", [("expiry", [0, 1]), ("staff", [2])])
def test_sorting_gift_cards_by_current_balance(
    search,
    indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    gift_card_list = [gift_card, gift_card_expiry_date, gift_card_used]
    variables = {"search": search}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == len(indexes)
    assert {card["node"]["code"] for card in data} == {
        card.code for card in gift_card_list
    }
