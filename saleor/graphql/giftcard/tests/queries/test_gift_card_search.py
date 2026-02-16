import graphene
import pytest

from saleor.giftcard.models import GiftCard
from saleor.giftcard.search import update_gift_cards_search_vector

from .....account.models import User
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


@pytest.mark.parametrize(
    ("search", "indexes"),
    [
        # Search by tag name
        ("test-tag", [0]),
        ("another-tag", [1]),
        ("tag", [0, 1, 2]),
        # Search by created_by email (customer_user creates [0,1], staff_user creates [2])
        ("staff_test@example.com", [2]),
        # Search by used_by email (customer_user is used_by for gift_card_used)
        # and created_by for others - should match all
        ("test@example.com", [0, 1, 2]),
        # Search by code
        ("never_expiry", [0]),  # gift_card code
        ("expiry_date", [1]),  # gift_card_expiry_date code
        # Search by last 3 characters of the code
        ("used", [2]),  # gift_card_used code
        # No match
        ("banana", []),
        ("nonexistent", []),
    ],
)
def test_query_gift_cards_with_search(
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
    update_gift_cards_search_vector(gift_card_list)
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
        gift_card_list[index].code for index in indexes
    }


def test_gift_cards_search_sorted_by_rank_exact_match_prioritized(
    staff_api_client,
    permission_manage_gift_card,
):
    # given
    user_exact = User.objects.create(
        first_name="Aaron", last_name="Smith", email="different@other.net"
    )
    user_prefix = User.objects.create(
        first_name="John", last_name="Doe", email="aaron00@example.net"
    )
    user_no_match = User.objects.create(
        first_name="Charlie", last_name="Brown", email="charlie@example.net"
    )

    gift_cards = GiftCard.objects.bulk_create(
        [
            GiftCard(
                code="GIFT0001AAAA",
                created_by=user_exact,
                created_by_email=user_exact.email,
                initial_balance_amount=100,
                current_balance_amount=100,
                currency="USD",
            ),
            GiftCard(
                code="GIFT0002BBBB",
                created_by=user_prefix,
                created_by_email=user_prefix.email,
                initial_balance_amount=100,
                current_balance_amount=100,
                currency="USD",
            ),
            GiftCard(
                code="GIFT0003CCCC",
                created_by=user_no_match,
                created_by_email=user_no_match.email,
                initial_balance_amount=100,
                current_balance_amount=100,
                currency="USD",
            ),
        ]
    )
    update_gift_cards_search_vector(gift_cards)

    variables = {
        "search": "aaron",
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]
    assert data["totalCount"] == 2

    returned_ids = [edge["node"]["id"] for edge in data["edges"]]
    gift_card_exact_id = graphene.Node.to_global_id("GiftCard", gift_cards[0].pk)
    gift_card_prefix_id = graphene.Node.to_global_id("GiftCard", gift_cards[1].pk)
    gift_card_no_match_id = graphene.Node.to_global_id("GiftCard", gift_cards[2].pk)

    # Exact name match "Aaron" should rank highest
    assert returned_ids[0] == gift_card_exact_id
    assert gift_card_prefix_id in returned_ids
    assert gift_card_no_match_id not in returned_ids
