from datetime import date, timedelta

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....core.enums import TimePeriodTypeEnum
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import GiftCardExpiryTypeEnum

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
    old_type = gift_card.expiry_type

    initial_balance = 100.0
    currency = gift_card.currency
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert data["expiryDate"] == date_value.isoformat()
    assert not data["expiryPeriod"]
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

    assert len(data["events"]) == 2
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
            "expiry": None,
        },
        {
            "type": GiftCardEvents.EXPIRY_SETTINGS_UPDATED.upper(),
            "user": {
                "email": staff_api_client.user.email,
            },
            "app": None,
            "balance": None,
            "expiry": {
                "expiryType": expiry_type.upper(),
                "oldExpiryType": old_type.upper(),
                "expiryPeriod": None,
                "oldExpiryPeriod": None,
                "expiryDate": date_value.isoformat(),
                "oldExpiryDate": None,
            },
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
    old_type = gift_card.expiry_type

    initial_balance = 100.0
    currency = gift_card.currency
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
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert data["expiryDate"] == date_value.isoformat()
    assert not data["expiryPeriod"]
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

    assert len(data["events"]) == 2
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
            "expiry": None,
        },
        {
            "type": GiftCardEvents.EXPIRY_SETTINGS_UPDATED.upper(),
            "user": None,
            "app": {"name": app_api_client.app.name},
            "balance": None,
            "expiry": {
                "expiryType": expiry_type.upper(),
                "oldExpiryType": old_type.upper(),
                "expiryPeriod": None,
                "oldExpiryPeriod": None,
                "expiryDate": date_value.isoformat(),
                "oldExpiryDate": None,
            },
        },
    ]
    for event in data["events"]:
        assert event in events


def test_update_gift_card_by_customer(api_client, customer_user, gift_card):
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


def test_update_gift_card_balance(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    old_initial_balance = float(gift_card.initial_balance.amount)
    old_current_balance = float(gift_card.current_balance.amount)

    initial_balance = 100.0
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
    assert data["expiryType"] == gift_card.expiry_type.upper()
    assert not data["expiryDate"]
    assert not data["expiryPeriod"]
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
        "expiry": None,
    }
    assert expected_event == data["events"][0]


def test_update_gift_card_change_to_expiry_period(
    staff_api_client,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_expiry_date
    old_type = gift_card.expiry_type
    old_expiry_date = gift_card.expiry_date

    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
    expiry_period = 2
    expiry_period_type = TimePeriodTypeEnum.YEAR.name
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expirySettings": {
                "expiryType": expiry_type,
                "expiryDate": None,
                "expiryPeriod": {
                    "type": expiry_period_type,
                    "amount": expiry_period,
                },
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert not data["expiryDate"]
    assert data["expiryPeriod"]["amount"] == expiry_period
    assert data["expiryPeriod"]["type"] == expiry_period_type
    assert data["tag"] == gift_card.tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email

    assert len(data["events"]) == 1
    expected_event = {
        "type": GiftCardEvents.EXPIRY_SETTINGS_UPDATED.upper(),
        "user": {
            "email": staff_api_client.user.email,
        },
        "app": None,
        "balance": None,
        "expiry": {
            "expiryType": expiry_type.upper(),
            "oldExpiryType": old_type.upper(),
            "expiryPeriod": {"amount": expiry_period, "type": expiry_period_type},
            "oldExpiryPeriod": None,
            "expiryDate": None,
            "oldExpiryDate": old_expiry_date.isoformat(),
        },
    }
    assert expected_event == data["events"][0]


def test_update_gift_card_change_to_never_expire(
    staff_api_client,
    gift_card_expiry_period,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_expiry_period
    old_type = gift_card.expiry_type
    old_expiry_period_type = gift_card.expiry_period_type
    old_expiry_period = gift_card.expiry_period

    expiry_type = GiftCardExpiryTypeEnum.NEVER_EXPIRE.name
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expirySettings": {
                "expiryType": expiry_type,
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert not data["expiryDate"]
    assert not data["expiryPeriod"]
    assert data["tag"] == gift_card.tag
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["createdByEmail"] == gift_card.created_by_email

    assert len(data["events"]) == 1
    expected_event = {
        "type": GiftCardEvents.EXPIRY_SETTINGS_UPDATED.upper(),
        "user": {
            "email": staff_api_client.user.email,
        },
        "app": None,
        "balance": None,
        "expiry": {
            "expiryType": expiry_type.upper(),
            "oldExpiryType": old_type.upper(),
            "oldExpiryPeriod": {
                "amount": old_expiry_period,
                "type": old_expiry_period_type.upper(),
            },
            "expiryPeriod": None,
            "expiryDate": None,
            "oldExpiryDate": None,
        },
    }
    assert expected_event == data["events"][0]


def test_update_used_gift_card_to_expiry_date(
    staff_api_client,
    gift_card_expiry_period,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_expiry_period
    date_value = date.today() + timedelta(days=365)

    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert data["expiryDate"] == date_value.isoformat()


def test_update_used_gift_card_to_expiry_period(
    staff_api_client,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_used

    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expirySettings": {
                "expiryType": expiry_type,
                "expiryPeriod": {
                    "type": TimePeriodTypeEnum.DAY.name,
                    "amount": 100,
                },
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryType"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_update_gift_card_negative_period_amount(
    staff_api_client,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card = gift_card_expiry_date

    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
    expiry_period = -10
    expiry_period_type = TimePeriodTypeEnum.YEAR.name
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
            "expirySettings": {
                "expiryType": expiry_type,
                "expiryPeriod": {
                    "type": expiry_period_type,
                    "amount": expiry_period,
                },
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryPeriod"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_update_gift_card_date_in_past(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
    date_value = date.today() - timedelta(days=365)
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "input": {
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
    errors = content["data"]["giftCardUpdate"]["errors"]
    data = content["data"]["giftCardUpdate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryDate"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name
