import graphene
import pytest

from .....giftcard.models import GiftCard
from ....tests.utils import get_graphql_content

FRAGMENT_EVENTS = """
    fragment GiftCardEvents on GiftCardEvent {
        id
        date
        type
        user {
            email
        }
        app {
            name
        }
        message
        email
        orderId
        orderNumber
        tags
        oldTags
        balance {
            initialBalance {
                amount
                currency
            }
            oldInitialBalance {
                amount
                currency
            }
            currentBalance {
                amount
                currency
            }
            oldCurrentBalance {
                amount
                currency
            }
        }
        expiryDate
        oldExpiryDate
    }
"""

FRAGMENT_GIFT_CARD_DETAILS = (
    FRAGMENT_EVENTS
    + """
        fragment GiftCardDetails on GiftCard {
            id
            code
            last4CodeChars
            isActive
            expiryDate
            tags {
                name
            }
            created
            lastUsedOn
            boughtInChannel
            initialBalance {
                currency
                amount
            }
            currentBalance {
                currency
                amount
            }
            createdBy {
                email
            }
            usedBy {
                email
            }
            createdByEmail
            usedByEmail
            app {
                name
            }
            product {
                name
            }
            events {
                ...GiftCardEvents
            }
        }
    """
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_gift_card_details(
    staff_api_client,
    gift_card,
    gift_card_event,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    count_queries,
):
    query = (
        FRAGMENT_GIFT_CARD_DETAILS
        + """
        query giftCard($id: ID!) {
            giftCard(id: $id){
                ...GiftCardDetails
            }
        }
    """
    )
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
    }
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=[
                permission_manage_gift_card,
                permission_manage_users,
                permission_manage_apps,
            ],
        )
    )

    assert content["data"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_query_gift_cards(
    staff_api_client,
    gift_cards_for_benchmarks,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
    count_queries,
):
    query = (
        FRAGMENT_GIFT_CARD_DETAILS
        + """
        query {
            giftCards(first: 20){
                edges {
                    node {
                        ...GiftCardDetails
                    }
                }
            }
        }
    """
    )
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {},
            permissions=[
                permission_manage_gift_card,
                permission_manage_apps,
                permission_manage_users,
            ],
        )
    )

    assert content["data"]
    assert len(content["data"]["giftCards"]["edges"]) == len(gift_cards_for_benchmarks)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_gift_cards_by_tags(
    staff_api_client,
    gift_cards_for_benchmarks,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
    count_queries,
):
    query = (
        FRAGMENT_GIFT_CARD_DETAILS
        + """
        query giftCards($filter: GiftCardFilterInput){
            giftCards(first: 20, filter: $filter) {
                edges {
                    node {
                        ...GiftCardDetails
                    }
                }
            }
        }
    """
    )
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {"filter": {"tags": ["benchmark-test-tag"]}},
            permissions=[
                permission_manage_gift_card,
                permission_manage_apps,
                permission_manage_users,
            ],
        )
    )

    assert content["data"]
    assert len(content["data"]["giftCards"]["edges"]) == len(gift_cards_for_benchmarks)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_gift_cards_by_used_by_user(
    staff_api_client,
    customer_user,
    gift_cards_for_benchmarks,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
    count_queries,
):
    cards_to_update = gift_cards_for_benchmarks[:10]
    for card in cards_to_update:
        card.used_by = customer_user
    GiftCard.objects.bulk_update(cards_to_update, ["used_by"])

    query = (
        FRAGMENT_GIFT_CARD_DETAILS
        + """
        query giftCards($filter: GiftCardFilterInput){
            giftCards(first: 20, filter: $filter) {
                edges {
                    node {
                        ...GiftCardDetails
                    }
                }
            }
        }
    """
    )
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            {
                "filter": {
                    "usedBy": [graphene.Node.to_global_id("User", customer_user.pk)]
                }
            },
            permissions=[
                permission_manage_gift_card,
                permission_manage_apps,
                permission_manage_users,
            ],
        )
    )

    assert content["data"]
    assert len(content["data"]["giftCards"]["edges"]) == len(cards_to_update)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_filter_gift_cards_by_products(
    staff_api_client,
    shippable_gift_card_product,
    gift_cards_for_benchmarks,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
    count_queries,
):
    cards_to_update = gift_cards_for_benchmarks[:10]
    for card in cards_to_update:
        card.product = shippable_gift_card_product
    GiftCard.objects.bulk_update(cards_to_update, ["product"])

    query = (
        FRAGMENT_GIFT_CARD_DETAILS
        + """
        query giftCards($filter: GiftCardFilterInput){
            giftCards(first: 20, filter: $filter) {
                edges {
                    node {
                        ...GiftCardDetails
                    }
                }
            }
        }
    """
    )
    variables = {
        "filter": {
            "products": [
                graphene.Node.to_global_id("Product", shippable_gift_card_product.pk)
            ]
        }
    }
    content = get_graphql_content(
        staff_api_client.post_graphql(
            query,
            variables,
            permissions=[
                permission_manage_gift_card,
                permission_manage_apps,
                permission_manage_users,
            ],
        )
    )

    assert content["data"]
    assert len(content["data"]["giftCards"]["edges"]) == len(cards_to_update)
