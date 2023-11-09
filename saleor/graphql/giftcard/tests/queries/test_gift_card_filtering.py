import graphene
import pytest

from .....giftcard.models import GiftCard
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

QUERY_GIFT_CARDS = """
    query giftCards($filter: GiftCardFilterInput){
        giftCards(first: 10, filter: $filter) {
            edges {
                node {
                    id
                    createdByEmail
                    last4CodeChars
                    product {
                        name
                    }
                    metadata {
                        key
                        value
                    }
                }
            }
            totalCount
        }
    }
"""


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [
        (["test-tag", "tag"], [0, 2]),
        (["another-tag"], [1]),
        (["tag", "test-tag", "another-tag"], [0, 1, 2]),
        (["not existing"], []),
        ([], [0, 1, 2]),
    ],
)
def test_query_filter_gift_cards_by_tags(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]
    variables = {"filter": {"tags": filter_value}}

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


def test_query_filter_gift_cards_by_products(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    shippable_gift_card_product,
    non_shippable_gift_card_product,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card.product = shippable_gift_card_product
    gift_card_used.product = shippable_gift_card_product
    gift_card_expiry_date.product = non_shippable_gift_card_product
    GiftCard.objects.bulk_update(
        [gift_card, gift_card_expiry_date, gift_card_used], ["product"]
    )

    variables = {
        "filter": {
            "products": [
                graphene.Node.to_global_id("Product", shippable_gift_card_product.pk)
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 2
    assert {card["node"]["id"] for card in data} == {
        graphene.Node.to_global_id("GiftCard", card.pk)
        for card in [gift_card, gift_card_used]
    }


def test_query_filter_gift_cards_by_used_by_user(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {
        "filter": {
            "usedBy": [graphene.Node.to_global_id("User", gift_card_used.used_by.pk)]
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 1
    assert data[0]["node"]["id"] == graphene.Node.to_global_id(
        "GiftCard", gift_card_used.pk
    )


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [("PLN", [0]), ("USD", [1, 2]), ("EUR", []), ("", [0, 1, 2])],
)
def test_query_filter_gift_cards_by_currency(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card.currency = "PLN"
    gift_card_used.currency = "USD"
    gift_card_expiry_date.currency = "USD"
    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]
    GiftCard.objects.bulk_update(gift_cards, ["currency"])

    variables = {"filter": {"currency": filter_value}}

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


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [
        (True, [0]),
        (False, [1, 2]),
    ],
)
def test_query_filter_gift_cards_by_is_active(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_card.is_active = True
    gift_card_used.is_active = False
    gift_card_expiry_date.is_active = False
    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]
    GiftCard.objects.bulk_update(gift_cards, ["is_active"])

    variables = {"filter": {"isActive": filter_value}}

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


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [
        (True, [2]),
        (False, [0, 1]),
    ],
)
def test_query_filter_gift_cards_used(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]

    variables = {"filter": {"used": filter_value}}

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


def test_query_filter_gift_cards_by_current_balance_no_currency_given(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {
        "filter": {
            "currentBalance": {
                "gte": "15",
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == "You must provide a `currency` filter parameter for filtering by price."
    )


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [
        ({"gte": 50}, [2]),
        ({"gte": 0, "lte": 50}, [0, 1]),
        ({"lte": 50}, [0, 1]),
        ({"gte": 90}, []),
        ({"lte": 5}, []),
        ({}, [0, 1, 2]),
    ],
)
def test_query_filter_gift_cards_by_current_balance(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]

    variables = {
        "filter": {"currentBalance": filter_value, "currency": gift_card.currency}
    }

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


def test_query_filter_gift_cards_by_initial_balance_no_currency_given(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {
        "filter": {
            "initialBalance": {
                "gte": "15",
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert (
        content["errors"][0]["message"]
        == "You must provide a `currency` filter parameter for filtering by price."
    )


@pytest.mark.parametrize(
    ("filter_value", "expected_gift_card_indexes"),
    [
        ({"gte": 90}, [2]),
        ({"gte": 0, "lte": 50}, [0, 1]),
        ({"lte": 50}, [0, 1]),
        ({"gte": 1100}, []),
        ({"lte": 5}, []),
        ({}, [0, 1, 2]),
    ],
)
def test_query_filter_gift_cards_by_initial_balance(
    filter_value,
    expected_gift_card_indexes,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    gift_cards = [
        gift_card,
        gift_card_expiry_date,
        gift_card_used,
    ]

    variables = {
        "filter": {"initialBalance": filter_value, "currency": gift_card.currency}
    }

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


def test_query_filter_gift_cards_by_code(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {"filter": {"code": gift_card.code}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 1
    assert data[0]["node"]["id"] == graphene.Node.to_global_id("GiftCard", gift_card.pk)


def test_query_filter_gift_cards_by_code_no_gift_card(
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {"filter": {"code": "code-does-not-exist"}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 0


def test_query_filter_gift_cards_by_metadata(
    staff_api_client,
    gift_card,
    gift_card_with_metadata,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS
    assert GiftCard.objects.count() == 2
    variables = {"filter": {"metadata": [{"key": "test", "value": "value"}]}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 1


def test_query_filter_gift_cards_by_created_by_email(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
):
    # given
    query = QUERY_GIFT_CARDS

    variables = {"filter": {"createdByEmail": gift_card.created_by_email}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_gift_card]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCards"]["edges"]
    assert len(data) == 1
    assert data[0]["node"]["createdByEmail"] == "test@example.com"
