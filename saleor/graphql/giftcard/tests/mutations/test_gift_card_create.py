import json
from datetime import date, timedelta
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from .....giftcard.models import GiftCard
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import assert_no_permission, get_graphql_content

CREATE_GIFT_CARD_MUTATION = """
    mutation giftCardCreate($input: GiftCardCreateInput!){
        giftCardCreate(input: $input) {
            giftCard {
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
                    message
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


@mock.patch(
    "saleor.graphql.giftcard.mutations.gift_card_create.send_gift_card_notification"
)
def test_create_never_expiry_gift_card(
    send_notification_mock,
    staff_api_client,
    customer_user,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
    gift_card_tag_list,
):
    # given
    initial_balance = 100
    currency = "USD"
    new_tag = "gift-card-tag"
    existing_tag_name = gift_card_tag_list[0].name
    tags = [new_tag, existing_tag_name]
    note = "This is gift card note that will be save in gift card event."
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "channel": channel_USD.slug,
            "addTags": tags,
            "note": note,
            "isActive": True,
        }
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
    assert data["last4CodeChars"]
    assert not data["expiryDate"]
    assert len(data["tags"]) == 2
    assert {tag["name"] for tag in data["tags"]} == set(tags)
    assert data["createdBy"]["email"] == staff_api_client.user.email
    assert data["createdByEmail"] == staff_api_client.user.email
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert not data["app"]
    assert not data["lastUsedOn"]
    assert data["isActive"]
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 2
    created_event, note_added = data["events"]

    assert created_event["type"] == GiftCardEvents.ISSUED.upper()
    assert created_event["user"]["email"] == staff_api_client.user.email
    assert not created_event["app"]
    assert created_event["balance"]["initialBalance"]["amount"] == initial_balance
    assert created_event["balance"]["initialBalance"]["currency"] == currency
    assert created_event["balance"]["currentBalance"]["amount"] == initial_balance
    assert created_event["balance"]["currentBalance"]["currency"] == currency
    assert not created_event["balance"]["oldInitialBalance"]
    assert not created_event["balance"]["oldCurrentBalance"]

    assert note_added["type"] == GiftCardEvents.NOTE_ADDED.upper()
    assert note_added["user"]["email"] == staff_api_client.user.email
    assert not note_added["app"]
    assert note_added["message"] == note

    gift_card = GiftCard.objects.get()
    send_notification_mock.assert_called_once_with(
        staff_api_client.user,
        None,
        customer_user,
        customer_user.email,
        gift_card,
        mock.ANY,
        channel_slug=channel_USD.slug,
        resending=False,
    )


@mock.patch(
    "saleor.graphql.giftcard.mutations.gift_card_create.send_gift_card_notification"
)
def test_create_gift_card_by_app(
    send_notification_mock,
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    note = "This is gift card note that will be save in gift card event."
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "addTags": [tag],
            "note": note,
            "expiryDate": None,
            "isActive": False,
        }
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
    assert data["last4CodeChars"]
    assert not data["expiryDate"]
    assert len(data["tags"]) == 1
    assert data["tags"][0]["name"] == tag
    assert not data["createdBy"]
    assert not data["createdByEmail"]
    assert not data["usedBy"]
    assert not data["usedByEmail"]
    assert data["app"]["name"] == app_api_client.app.name
    assert not data["lastUsedOn"]
    assert data["isActive"] is False
    assert data["initialBalance"]["amount"] == initial_balance
    assert data["currentBalance"]["amount"] == initial_balance

    assert len(data["events"]) == 2
    created_event, note_added = data["events"]

    assert created_event["type"] == GiftCardEvents.ISSUED.upper()
    assert not created_event["user"]
    assert created_event["app"]["name"] == app_api_client.app.name
    assert created_event["balance"]["initialBalance"]["amount"] == initial_balance
    assert created_event["balance"]["initialBalance"]["currency"] == currency
    assert created_event["balance"]["currentBalance"]["amount"] == initial_balance
    assert created_event["balance"]["currentBalance"]["currency"] == currency
    assert not created_event["balance"]["oldInitialBalance"]
    assert not created_event["balance"]["oldCurrentBalance"]

    assert note_added["type"] == GiftCardEvents.NOTE_ADDED.upper()
    assert not note_added["user"]
    assert note_added["app"]["name"] == app_api_client.app.name
    assert note_added["message"] == note

    send_notification_mock.assert_not_called()


def test_create_gift_card_by_customer(api_client, customer_user, channel_USD):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "channel": channel_USD.slug,
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "expiryDate": None,
            "isActive": True,
        }
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
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "expiryDate": None,
            "isActive": True,
        }
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
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "isActive": True,
        }
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


def test_create_gift_card_with_malformed_email(
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 10
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": "malformed",
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "isActive": True,
        }
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
    errors = content["data"]["giftCardCreate"]["errors"]

    assert not data
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "email"
    assert error["code"] == GiftCardErrorCode.INVALID.name


def test_create_gift_card_lack_of_channel(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 10
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "isActive": True,
        }
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
    errors = content["data"]["giftCardCreate"]["errors"]

    assert not data
    assert len(errors) == 1
    error = errors[0]
    assert error["field"] == "channel"
    assert error["code"] == GiftCardErrorCode.REQUIRED.name


def test_create_gift_card_with_zero_balance_amount(
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": 0,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "isActive": True,
        }
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


@mock.patch(
    "saleor.graphql.giftcard.mutations.gift_card_create.send_gift_card_notification"
)
def test_create_gift_card_with_expiry_date(
    send_notification_mock,
    staff_api_client,
    customer_user,
    channel_USD,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    date_value = date.today() + timedelta(days=365)
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "channel": channel_USD.slug,
            "addTags": [tag],
            "expiryDate": date_value,
            "isActive": True,
        }
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
    assert data["last4CodeChars"]
    assert data["expiryDate"] == date_value.isoformat()

    assert len(data["events"]) == 1
    created_event = data["events"][0]

    assert created_event["type"] == GiftCardEvents.ISSUED.upper()
    assert created_event["user"]["email"] == staff_api_client.user.email
    assert not created_event["app"]
    assert created_event["balance"]["initialBalance"]["amount"] == initial_balance
    assert created_event["balance"]["initialBalance"]["currency"] == currency
    assert created_event["balance"]["currentBalance"]["amount"] == initial_balance
    assert created_event["balance"]["currentBalance"]["currency"] == currency
    assert not created_event["balance"]["oldInitialBalance"]
    assert not created_event["balance"]["oldCurrentBalance"]

    gift_card = GiftCard.objects.get()
    send_notification_mock.assert_called_once_with(
        staff_api_client.user,
        None,
        customer_user,
        customer_user.email,
        gift_card,
        mock.ANY,
        channel_slug=channel_USD.slug,
        resending=False,
    )


@pytest.mark.parametrize("date_value", [date(1999, 1, 1), date.today()])
def test_create_gift_card_with_expiry_date_type_invalid(
    date_value,
    staff_api_client,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "userEmail": customer_user.email,
            "addTags": [tag],
            "note": "This is gift card note that will be save in gift card event.",
            "expiryDate": date_value,
            "isActive": True,
        }
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


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_gift_card_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    app_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    note = "This is gift card note that will be save in gift card event."
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "addTags": [tag],
            "note": note,
            "expiryDate": None,
            "isActive": False,
        }
    }

    # when
    response = app_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    gift_card = GiftCard.objects.last()

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
                "is_active": gift_card.is_active,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: app_api_client.app)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.GIFT_CARD_CREATED,
        [any_webhook],
        gift_card,
        SimpleLazyObject(lambda: app_api_client.app),
    )


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_gift_card_with_email_triggers_gift_card_sent_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    app_api_client,
    channel_USD,
    customer_user,
    permission_manage_gift_card,
    permission_manage_users,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    initial_balance = 100
    currency = "USD"
    tag = "gift-card-tag"
    note = "This is gift card note that will be save in gift card event."
    variables = {
        "input": {
            "balance": {
                "amount": initial_balance,
                "currency": currency,
            },
            "addTags": [tag],
            "note": note,
            "expiryDate": None,
            "isActive": False,
            "channel": channel_USD.slug,
            "userEmail": customer_user.email,
        }
    }

    # when
    response = app_api_client.post_graphql(
        CREATE_GIFT_CARD_MUTATION,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )
    gift_card = GiftCard.objects.last()

    # then
    content = get_graphql_content(response)
    errors = content["data"]["giftCardCreate"]["errors"]
    data = content["data"]["giftCardCreate"]["giftCard"]

    assert not errors
    assert data["code"]

    mocked_webhook_trigger.assert_any_call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("GiftCard", gift_card.id),
                "is_active": gift_card.is_active,
                "channel_slug": channel_USD.slug,
                "sent_to_email": customer_user.email,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: app_api_client.app)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.GIFT_CARD_SENT,
        [any_webhook],
        {
            "gift_card": gift_card,
            "channel_slug": channel_USD.slug,
            "sent_to_email": customer_user.email,
        },
        SimpleLazyObject(lambda: app_api_client.app),
    )


def test_create_gift_card_with_code(
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    code = "custom-code"
    variables = {
        "input": {
            "balance": {
                "amount": 1,
                "currency": "USD",
            },
            "code": code,
            "isActive": True,
        }
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
    assert data["code"] == code


def test_create_gift_card_with_to_short_code(
    staff_api_client,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    code = "short"
    variables = {
        "input": {
            "balance": {
                "amount": 1,
                "currency": "USD",
            },
            "code": code,
            "isActive": True,
        }
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
    assert errors[0]["field"] == "code"
    assert errors[0]["code"] == "INVALID"
