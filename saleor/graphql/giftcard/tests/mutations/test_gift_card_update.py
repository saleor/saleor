from datetime import date, timedelta

import graphene
import pytest

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content

UPDATE_GIFT_CARD_MUTATION = """
    mutation giftCardUpdate(
        $id: ID!, $input: GiftCardUpdateInput!
    ){
        giftCardUpdate(id: $id, input: $input) {
            giftCard {
                id
                last4
                isActive
                expiryDate
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
                    tag
                    oldTag
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
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_update_gift_card(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    old_initial_balance = float(gift_card.initial_balance.amount)
    old_current_balance = float(gift_card.current_balance.amount)
    old_tag = gift_card.tag

    initial_balance = 100.0
    currency = gift_card.currency
    date_value = date.today() + timedelta(days=365)
    tag = "new-gift-card-tag"
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
            "tag": tag,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert data["expiryDate"] == date_value.isoformat()
    assert data["tag"] == tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert not data["app"]
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 3
    events = [
        {
            "type": GiftCardEvents.BALANCE_RESET.upper(),
            "user": {
                "email": staff_api_client.user.email,
            },
            "app": None,
            "balance": {
                "initialBalance": {
                    "amount": initial_balance,
                    "currency": currency,
                },
                "currentBalance": {
                    "amount": initial_balance,
                    "currency": currency,
                },
                "oldInitialBalance": {
                    "amount": old_initial_balance,
                    "currency": currency,
                },
                "oldCurrentBalance": {
                    "amount": old_current_balance,
                    "currency": currency,
                },
            },
            "expiryDate": None,
            "oldExpiryDate": None,
            "tag": None,
            "oldTag": None,
        },
        {
            "type": GiftCardEvents.EXPIRY_DATE_UPDATED.upper(),
            "user": {
                "email": staff_api_client.user.email,
            },
            "app": None,
            "balance": None,
            "expiryDate": date_value.isoformat(),
            "oldExpiryDate": None,
            "tag": None,
            "oldTag": None,
        },
        {
            "type": GiftCardEvents.TAG_UPDATED.upper(),
            "user": {
                "email": staff_api_client.user.email,
            },
            "app": None,
            "balance": None,
            "expiryDate": None,
            "oldExpiryDate": None,
            "tag": tag,
            "oldTag": old_tag,
        },
    ]
    for event in data["events"]:
        assert event in events


def test_update_gift_card_by_app(
    app_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    old_initial_balance = float(gift_card.initial_balance.amount)
    old_current_balance = float(gift_card.current_balance.amount)
    old_tag = gift_card.tag

    initial_balance = 100.0
    currency = gift_card.currency
    date_value = date.today() + timedelta(days=365)
    tag = "new-gift-card-tag"
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
            "tag": tag,
            "expiryDate": date_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert data["expiryDate"] == date_value.isoformat()
    assert data["tag"] == tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert not data["app"]
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 3
    events = [
        {
            "type": GiftCardEvents.BALANCE_RESET.upper(),
            "user": None,
            "app": {"name": app_api_client.app.name},
            "balance": {
                "initialBalance": {
                    "amount": initial_balance,
                    "currency": currency,
                },
                "currentBalance": {
                    "amount": initial_balance,
                    "currency": currency,
                },
                "oldInitialBalance": {
                    "amount": old_initial_balance,
                    "currency": currency,
                },
                "oldCurrentBalance": {
                    "amount": old_current_balance,
                    "currency": currency,
                },
            },
            "expiryDate": None,
            "oldExpiryDate": None,
            "tag": None,
            "oldTag": None,
        },
        {
            "type": GiftCardEvents.EXPIRY_DATE_UPDATED.upper(),
            "user": None,
            "app": {"name": app_api_client.app.name},
            "balance": None,
            "expiryDate": date_value.isoformat(),
            "oldExpiryDate": None,
            "tag": None,
            "oldTag": None,
        },
        {
            "type": GiftCardEvents.TAG_UPDATED.upper(),
            "user": None,
            "app": {"name": app_api_client.app.name},
            "balance": None,
            "expiryDate": None,
            "oldExpiryDate": None,
            "tag": tag,
            "oldTag": old_tag,
        },
    ]
    for event in data["events"]:
        assert event in events


def test_update_gift_card_by_customer(api_client, gift_card):
    # given
    initial_balance = 100.0
    tag = "new-gift-card-tag"
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
            "tag": tag,
        },
    }

    # when
    response = api_client.post_graphql(
        UPDATE_GIFT_CARD_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


@pytest.mark.parametrize("initial_balance", [100.0, 0.0])
def test_update_gift_card_balance(
    initial_balance,
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    old_initial_balance = float(gift_card.initial_balance.amount)
    old_current_balance = float(gift_card.current_balance.amount)

    currency = gift_card.currency
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "balanceAmount": initial_balance,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert not data["expiryDate"]
    assert data["tag"] == gift_card.tag
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 1
    expected_event = {
        "type": GiftCardEvents.BALANCE_RESET.upper(),
        "user": {
            "email": staff_api_client.user.email,
        },
        "app": None,
        "balance": {
            "initialBalance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "currentBalance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "oldInitialBalance": {
                "amount": old_initial_balance,
                "currency": currency,
            },
            "oldCurrentBalance": {
                "amount": old_current_balance,
                "currency": currency,
            },
        },
        "expiryDate": None,
        "oldExpiryDate": None,
        "tag": None,
        "oldTag": None,
    }
    assert expected_event == data["events"][0]


def test_update_gift_card_change_to_never_expire(
    staff_api_client,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_expiry_date
    old_expiry_date = gift_card.expiry_date

    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expiryDate": None,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert not data["expiryDate"]
    assert data["tag"] == gift_card.tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email

    assert len(data["events"]) == 1
    expected_event = {
        "type": GiftCardEvents.EXPIRY_DATE_UPDATED.upper(),
        "user": {
            "email": staff_api_client.user.email,
        },
        "app": None,
        "balance": None,
        "expiryDate": None,
        "tag": None,
        "oldTag": None,
        "oldExpiryDate": old_expiry_date.isoformat(),
    }
    assert expected_event == data["events"][0]


def test_update_used_gift_card_to_expiry_date(
    staff_api_client,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_used
    date_value = date.today() + timedelta(days=365)

    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert data["expiryDate"] == date_value.isoformat()
    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["expiryDate"] == date_value.isoformat()
    assert event["oldExpiryDate"] is None


def test_update_used_gift_card_to_never_expired(
    staff_api_client,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_used

    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expiryDate": None,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert data["expiryDate"] is None


def test_update_gift_card_date_in_past(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    date_value = date.today() - timedelta(days=365)
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryDate"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_update_gift_card_expired_card(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expiryDate": None,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["last4"]
    assert not data["expiryDate"]
    assert data["tag"] == gift_card.tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email

    assert len(data["events"]) == 1
    assert data["events"][0]["type"] == GiftCardEvents.EXPIRY_DATE_UPDATED.upper()
