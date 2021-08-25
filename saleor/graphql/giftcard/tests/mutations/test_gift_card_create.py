from datetime import date, timedelta

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....core.enums import TimePeriodTypeEnum
from ....tests.utils import assert_no_permission, get_graphql_content
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


def test_create_never_expiry_gift_card(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert not data["expiryDate"]
    assert not data["expiryPeriod"]
    assert data["tag"] == tag
    assert data["createdBy"]["email"] == staff_api_client.user.email
    assert data["createdByEmail"] == staff_api_client.user.email
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert not data["app"]
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["type"] == GiftCardEvents.ISSUED.upper()
    assert event["user"]["email"] == staff_api_client.user.email
    assert not event["app"]
    assert event["balance"]["initialBalance"]["amount"] == initial_balance
    assert event["balance"]["initialBalance"]["currency"] == currency
    assert event["balance"]["currentBalance"]["amount"] == initial_balance
    assert event["balance"]["currentBalance"]["currency"] == currency
    assert not event["balance"]["oldInitialBalance"]
    assert not event["balance"]["oldCurrentBalance"]


def test_create_gift_card_by_app(
    app_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
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
            "expiryDate": None,
        },
    }

    # when
    response = app_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert not data["expiryDate"]
    assert not data["expiryPeriod"]
    assert data["tag"] == tag
    assert not data["createdBy"]
    assert not data["createdByEmail"]
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert data["app"]["name"] == app_api_client.app.name
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["type"] == GiftCardEvents.ISSUED.upper()
    assert not event["user"]
    assert event["app"]["name"] == app_api_client.app.name
    assert event["balance"]["initialBalance"]["amount"] == initial_balance
    assert event["balance"]["initialBalance"]["currency"] == currency
    assert event["balance"]["currentBalance"]["amount"] == initial_balance
    assert event["balance"]["currentBalance"]["currency"] == currency
    assert not event["balance"]["oldInitialBalance"]
    assert not event["balance"]["oldCurrentBalance"]


def test_create_gift_card_by_customer(api_client, customer_user):
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
            "expiryDate": None,
        },
    }

    # when
    response = api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_create_gift_card_no_premissions(staff_api_client):
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
        "tag": tag,
        "note": "This is gift card note that will be save in gift card event.",
        "expirySettings": {
            "expiryType": expiry_type,
            "expiryDate": None,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
    )

    # then
    assert_no_permission(response)


def test_create_gift_card_with_too_many_decimal_places_in_balance_amount(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 10.123
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "balance"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_card_with_expiry_date(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
    date_value = date.today() + timedelta(days=365)
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
            "expiryDate": date_value,
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert data["expiryDate"] == date_value.isoformat()
    assert not data["expiryPeriod"]

    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["type"] == GiftCardEvents.ISSUED.upper()
    assert event["user"]["email"] == staff_api_client.user.email


def test_create_gift_card_with_expiry_date_type_date_not_given(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryDate"
    assert errors[0]["code"] == GiftCardErrorCode.REQUIRED.name


def test_create_gift_card_with_expiry_date_type_date_in_past(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_DATE.name
    date_value = date(1999, 1, 1)
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
            "expiryDate": date_value,
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryDate"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_card_with_expiry_period(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
    tag = "gift-card-tag"
    period_amount = 10
    period_type = TimePeriodTypeEnum.MONTH.name
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
            "expiryPeriod": {
                "type": period_type,
                "amount": period_amount,
            },
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]
    assert data["displayCode"]
    assert data["expiryType"] == expiry_type.upper()
    assert not data["expiryDate"]
    assert data["expiryPeriod"]["amount"] == period_amount
    assert data["expiryPeriod"]["type"] == period_type

    assert len(data["events"]) == 1
    event = data["events"][0]
    assert event["type"] == GiftCardEvents.ISSUED.upper()
    assert event["user"]["email"] == staff_api_client.user.email


def test_create_gift_card_with_expiry_period_negative_amount(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
    tag = "gift-card-tag"
    period_amount = -10
    period_type = TimePeriodTypeEnum.MONTH.name
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
            "expiryPeriod": {
                "type": period_type,
                "amount": period_amount,
            },
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryPeriod"
    assert errors[0]["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_card_with_expiry_period_type_period_data_not_given(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    expiry_type = GiftCardExpiryTypeEnum.EXPIRY_PERIOD.name
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
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not data
    assert len(errors) == 1
    assert errors[0]["field"] == "expiryPeriod"
    assert errors[0]["code"] == GiftCardErrorCode.REQUIRED.name
