from datetime import date, timedelta

import graphene
import pytest

from ....tests.utils import get_graphql_content
from ...enums import GiftCardExpiryTypeEnum

CREATE_GIFT_CARD_MUTATION = """
    mutation giftCardCreate(
        $balance: PriceInput!, $userEmail: String, $tag: String,
        $expirySettings: GiftCardExpirySettingsInput!, $note: String
    ){
        giftCardCreate(input: {
                balance: $balance, userEmail: $userEmail, tag: $tag,
                expirySettings: $expirySettings, note: $note }) {
            giftCard {
                id
                code
                displayCode
                isActive
                expiryDate
                expiryType
                expiryPeriod {
                    amount
                    type
                }
                tag
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
                    type
                    user {
                        email
                    }
                    app {
                        name
                    }
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_create_never_expiry_gift_card(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    count_queries,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.NEVER_EXPIRE.name
    tag = "gift-card-tag"
    variables = {
        "balance": {
            "amount": initial_balance,
            "currency": currency,
        },
        "userEmail": customer_user.email,
        "tag": tag,
        "note": "This is gift card note that will be save in gift card event.",
        "expirySettings": {
            "expiryType": expiry_type,
        },
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


UPDATE_GIFT_CARD_MUTATION = """
    mutation giftCardUpdate(
        $id: ID!, $input: GiftCardUpdateInput!
    ){
        giftCardUpdate(id: $id, input: $input) {
            giftCard {
                id
                code
                displayCode
                isActive
                expiryDate
                expiryType
                expiryPeriod {
                    amount
                    type
                }
                tag
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
                    type
                    user {
                        email
                    }
                    app {
                        name
                    }
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
                    expiry {
                        expiryType
                        oldExpiryType
                        expiryPeriod {
                            type
                            amount
                        }
                        oldExpiryPeriod {
                            type
                            amount
                        }
                        expiryDate
                        oldExpiryDate
                    }
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
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
    date_value = date.today() + timedelta(days=365)
    tag = "new-gift-card-tag"
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
            "tag": tag,
            "expirySettings": {
                "expiryType": expiry_type,
                "expiryDate": date_value,
            },
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
