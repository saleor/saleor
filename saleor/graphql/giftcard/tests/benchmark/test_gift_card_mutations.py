from datetime import date, timedelta

import graphene
import pytest

from .....giftcard.models import GiftCard
from ....tests.utils import get_graphql_content
from .test_gift_card_queries import FRAGMENT_GIFT_CARD_DETAILS

CREATE_GIFT_CARD_MUTATION = (
    FRAGMENT_GIFT_CARD_DETAILS
    + """
    mutation giftCardCreate(
        $balance: PriceInput!, $userEmail: String, $addTags: [String!],
         $channel: String, $note: String, $expiryDate: Date, $isActive: Boolean!
    ){
        giftCardCreate(input: {
                balance: $balance, userEmail: $userEmail, addTags: $addTags,
                channel: $channel, expiryDate: $expiryDate, note: $note,
                isActive: $isActive
        }) {
            giftCard {
                ...GiftCardDetails
            }
            errors {
                field
                message
                code
            }
        }
    }
"""
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_never_expiry_gift_card(
    staff_api_client,
    customer_user,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    count_queries,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "balance": {
            "amount": initial_balance,
            "currency": currency,
        },
        "userEmail": customer_user.email,
        "channel": channel_USD.slug,
        "addTags": [tag],
        "note": "This is gift card note that will be save in gift card event.",
        "expiry_date": None,
        "isActive": True,
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert data


UPDATE_GIFT_CARD_MUTATION = (
    FRAGMENT_GIFT_CARD_DETAILS
    + """
    mutation giftCardUpdate(
        $id: ID!, $input: GiftCardUpdateInput!
    ){
        giftCardUpdate(id: $id, input: $input) {
            giftCard {
                ...GiftCardDetails
            }
            errors {
                field
                message
                code
            }
        }
    }
"""
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_update_gift_card(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    count_queries,
):
    # given
    initial_balance = 100.0
    date_value = date.today() + timedelta(days=365)
    old_tag = gift_card.tags.first()
    tag = "new-gift-card-tag"
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
            "addTags": [tag],
            "removeTags": [old_tag.name],
            "expiryDate": date_value,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardUpdate"]["giftCard"]
    assert data


MUTATION_GIFT_CARD_BULK_ACTIVATE = """
    mutation GiftCardBulkActivate($ids: [ID!]!) {
        giftCardBulkActivate(ids: $ids) {
            count
            errors {
                code
                field
            }
        }
    }
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_gift_card_bulk_activate_by_staff(
    staff_api_client,
    gift_cards_for_benchmarks,
    permission_manage_gift_card,
    count_queries,
):
    # given
    for card in gift_cards_for_benchmarks:
        card.is_active = False
    GiftCard.objects.bulk_update(gift_cards_for_benchmarks, ["is_active"])

    ids = [
        graphene.Node.to_global_id("GiftCard", card.pk)
        for card in gift_cards_for_benchmarks
    ]
    variables = {"ids": ids}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_ACTIVATE,
        variables,
        permissions=(permission_manage_gift_card,),
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["giftCardBulkActivate"]["count"] == len(ids)


MUTATION_GIFT_CARD_BULK_CREATE = (
    FRAGMENT_GIFT_CARD_DETAILS
    + """
    mutation GiftCardBulkCreate($input: GiftCardBulkCreateInput!) {
        giftCardBulkCreate(input: $input) {
            count
            giftCards {
                ...GiftCardDetails
            }
            errors {
                code
                field
            }
        }
    }
"""
)


def test_bulk_create_gift_cards(
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    count = 10
    is_active = True
    variables = {
        "input": {
            "count": count,
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "tags": [tag],
            "isActive": is_active,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_GIFT_CARD_BULK_CREATE,
        variables,
        permissions=(
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ),
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["giftCardBulkCreate"]["count"] == count
