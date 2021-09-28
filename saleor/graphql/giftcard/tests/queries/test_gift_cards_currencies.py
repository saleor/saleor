from .....giftcard.models import GiftCard
from ....tests.utils import assert_no_permission, get_graphql_content

QUERY_GIFT_CARD_CURRENCIES = """
    query {
        giftCardCurrencies
    }
"""


def test_fetch_gift_card_currencies(
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    staff_api_client,
    permission_manage_gift_card,
):
    # given
    gift_card_expiry_date.currency = "PLN"
    gift_card_used.currency = "EUR"
    GiftCard.objects.bulk_update([gift_card_expiry_date, gift_card_used], ["currency"])

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_CURRENCIES,
        permissions=[
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardCurrencies"]
    assert set(data) == {gift_card.currency, "PLN", "EUR"}


def test_fetch_gift_card_currencies_by_app(
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    app_api_client,
    permission_manage_gift_card,
):
    # given
    gift_card_used.currency = "EUR"
    gift_card_used.save(update_fields=["currency"])

    # when
    response = app_api_client.post_graphql(
        QUERY_GIFT_CARD_CURRENCIES,
        permissions=[
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardCurrencies"]
    assert set(data) == {gift_card.currency, gift_card_expiry_date.currency, "EUR"}


def test_fetch_gift_card_currencies_no_permission(api_client):
    # when
    response = api_client.post_graphql(
        QUERY_GIFT_CARD_CURRENCIES,
    )

    # then
    assert_no_permission(response)


def test_fetch_gift_card_currencies_no_gift_cards(
    staff_api_client, permission_manage_gift_card
):
    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_CURRENCIES,
        permissions=[
            permission_manage_gift_card,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCardCurrencies"]
    assert data == []
