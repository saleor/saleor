from datetime import date

from ....tests.utils import get_graphql_content

CREATE_GIFT_CARD_MUTATION = """
    mutation giftCardCreate(
        $startDate: Date, $endDate: Date, $expiryDate: Date, $channel: String,
        $balance: PriceInput!, $userEmail: String, $isActive: Boolean!
    ){
        giftCardCreate(input: {
                startDate: $startDate,
                endDate: $endDate,
                balance: $balance, userEmail: $userEmail, channel: $channel
                expiryDate: $expiryDate, isActive: $isActive
            }) {
            giftCard {
                id
                code
                last4CodeChars
                isActive
                startDate
                endDate
                expiryDate
                tags {
                    name
                }
                created
                lastUsedOn
                initialBalance {
                    currency
                    amount
                }
                currentBalance {
                    currency
                    amount
                }
                user {
                    email
                }
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_create_never_expiry_gift_card(
    staff_api_client,
    customer_user,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    start_date = date(day=1, month=1, year=2018)
    end_date = date(day=1, month=1, year=2019)
    initial_balance = 100
    variables = {
        "balance": {
            "amount": initial_balance,
            "currency": currency,
        },
        "userEmail": customer_user.email,
        "channel": channel_USD.slug,
        "tags": [tag],
        "note": "This is gift card note that will be save in gift card event.",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "isActive": True,
    }
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["last4CodeChars"]
    assert data["user"]["email"] == staff_api_client.user.email
    assert data["startDate"] is None
    assert data["endDate"] is None
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance
