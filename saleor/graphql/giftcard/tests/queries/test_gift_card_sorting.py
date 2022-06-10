import datetime

import graphene
import pytest
from django.utils import timezone

from .....giftcard.models import GiftCard
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_GIFT_CARDS = """
    query giftCards($sortBy: GiftCardSortingInput,  $filter: GiftCardFilterInput){
        giftCards(first: 10, filter: $filter, sortBy: $sortBy) {
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


@pytest.mark.parametrize(
    "direction",
    ("ASC", "DESC"),
)
def test_sorting_gift_cards_by_current_balance(
    direction,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    variables = {
        "sortBy": {
            "direction": direction,
            "field": "CURRENT_BALANCE",
        },
        "filter": {
            "currency": gift_card.currency,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    gift_card_list = [gift_card, gift_card_expiry_date, gift_card_used]
    if direction == "DESC":
        gift_card_list.reverse()

    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 3
    assert [card["node"]["id"] for card in data] == [
        graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_card_list
    ]


def test_sorting_gift_cards_by_current_balance_no_currency_in_filter(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    variables = {
        "sortBy": {
            "direction": "ASC",
            "field": "CURRENT_BALANCE",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == "Sorting by balance requires filtering by currency."
    )


@pytest.mark.parametrize(
    "direction",
    ("ASC", "DESC"),
)
def test_sorting_gift_cards_by_product(
    direction,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    non_shippable_gift_card_product,
    shippable_gift_card_product,
    permission_manage_gift_card,
):
    # given
    gift_card.product = non_shippable_gift_card_product
    gift_card_expiry_date.product = shippable_gift_card_product
    gift_card_used.product = None
    gift_card_list = [gift_card, gift_card_expiry_date, gift_card_used]
    GiftCard.objects.bulk_update(gift_card_list, ["product"])

    variables = {
        "sortBy": {
            "direction": direction,
            "field": "PRODUCT",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    if direction == "DESC":
        gift_card_list.reverse()

    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 3
    assert [card["node"]["id"] for card in data] == [
        graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_card_list
    ]


@pytest.mark.parametrize(
    "direction",
    ("ASC", "DESC"),
)
def test_sorting_gift_cards_by_used_by(
    direction,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    gift_card.created_at = timezone.now() - datetime.timedelta(days=10)
    gift_card_expiry_date.created_at = timezone.now()
    gift_card_list = [gift_card_used, gift_card, gift_card_expiry_date]
    GiftCard.objects.bulk_update(gift_card_list, ["created_at"])

    variables = {
        "sortBy": {
            "direction": direction,
            "field": "USED_BY",
        }
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARDS, variables, permissions=[permission_manage_gift_card]
    )

    # then
    if direction == "DESC":
        gift_card_list.reverse()

    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 3
    assert [card["node"]["id"] for card in data] == [
        graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_card_list
    ]
