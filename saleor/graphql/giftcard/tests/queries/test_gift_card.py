import datetime

import graphene
from django.utils import timezone

from .....core import TimePeriodType
from .....giftcard import GiftCardEvents, GiftCardExpiryType
from .....giftcard.models import GiftCardEvent
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_GIFT_CARD_BY_ID = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
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
        }
    }
"""


def test_query_gift_card_with_permissions(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["code"] == gift_card.code
    assert data["displayCode"] == gift_card.display_code
    assert data["isActive"] == gift_card.is_active
    assert data["expiryDate"] is None
    assert data["expiryType"] == gift_card.expiry_type.upper()
    assert data["expiryPeriod"] is None
    assert data["tag"] == gift_card.tag
    assert data["created"] == gift_card.created.isoformat()
    assert data["lastUsedOn"] == gift_card.last_used_on
    assert data["initialBalance"]["currency"] == gift_card.initial_balance.currency
    assert data["initialBalance"]["amount"] == gift_card.initial_balance.amount
    assert data["currentBalance"]["currency"] == gift_card.current_balance.currency
    assert data["currentBalance"]["amount"] == gift_card.current_balance.amount
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["usedBy"] is None
    assert data["createdByEmail"] == gift_card.created_by_email
    assert data["usedByEmail"] == gift_card.used_by_email
    assert data["product"] is None
    assert data["app"] is None


def test_query_gift_card_no_permissions(staff_api_client, gift_card):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_gift_card_by_app(
    app_api_client,
    gift_card_expiry_period,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_expiry_period.pk)
    variables = {"id": gift_card_id}

    # when
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["code"] == gift_card_expiry_period.code
    assert data["displayCode"] == gift_card_expiry_period.display_code
    assert data["isActive"] == gift_card_expiry_period.is_active
    assert data["expiryDate"] is None
    assert data["expiryType"] == gift_card_expiry_period.expiry_type.upper()
    assert data["expiryPeriod"]["amount"] == gift_card_expiry_period.expiry_period
    assert (
        data["expiryPeriod"]["type"]
        == gift_card_expiry_period.expiry_period_type.upper()
    )
    assert data["tag"] == gift_card_expiry_period.tag
    assert data["created"] == gift_card_expiry_period.created.isoformat()
    assert data["lastUsedOn"] == gift_card_expiry_period.last_used_on
    assert (
        data["initialBalance"]["currency"]
        == gift_card_expiry_period.initial_balance.currency
    )
    assert (
        data["initialBalance"]["amount"]
        == gift_card_expiry_period.initial_balance.amount
    )
    assert (
        data["currentBalance"]["currency"]
        == gift_card_expiry_period.current_balance.currency
    )
    assert (
        data["currentBalance"]["amount"]
        == gift_card_expiry_period.current_balance.amount
    )
    assert data["createdBy"]["email"] == gift_card_expiry_period.created_by.email
    assert data["usedBy"] is None
    assert data["createdByEmail"] == gift_card_expiry_period.created_by_email
    assert data["usedByEmail"] == gift_card_expiry_period.used_by_email
    assert data["product"] is None
    assert data["app"] is None


def test_query_gift_card_by_app_no_premissions(
    app_api_client, gift_card_created_by_staff
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_created_by_staff.pk)
    variables = {"id": gift_card_id}

    # when
    response = app_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_gift_card_with_expiry_date(
    staff_api_client,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_expiry_date.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["code"] == gift_card_expiry_date.code
    assert data["displayCode"] == gift_card_expiry_date.display_code
    assert data["expiryDate"] == gift_card_expiry_date.expiry_date.isoformat()
    assert data["expiryType"] == gift_card_expiry_date.expiry_type.upper()
    assert data["expiryPeriod"] is None


def test_query_gift_card_by_customer(
    api_client, gift_card, permission_manage_gift_card
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # when
    # Query should fail without manage_users permission.
    response = api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_query_used_gift_card_no_permission(
    staff_api_client,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    assert_no_permission(response)


def test_query_used_gift_card_by_owner(
    staff_api_client,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card_used.used_by = staff_api_client.user
    gift_card_used.save(update_fields=["used_by"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card_used.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["code"] == gift_card_used.code
    assert data["usedBy"]["email"] == gift_card_used.used_by.email


def test_query_gift_card_only_users_emails(
    staff_api_client,
    gift_card,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID
    gift_card.used_by = None
    gift_card.created_by = None
    gift_card.save(update_fields=["used_by", "created_by"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
            permission_manage_apps,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["code"] == gift_card.code
    assert data["createdBy"] is None
    assert data["usedBy"] is None
    assert data["createdByEmail"] == gift_card.created_by_email
    assert data["usedByEmail"] == gift_card.used_by_email


def test_staff_query_gift_card_by_invalid_id(
    staff_api_client, gift_card, permission_manage_users, permission_manage_gift_card
):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_BY_ID,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    content = get_graphql_content_from_response(response)
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Couldn't resolve id: {id}."
    assert content["data"]["giftCard"] is None


def test_staff_query_gift_card_with_invalid_object_type(
    staff_api_client, gift_card, permission_manage_users, permission_manage_gift_card
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_BY_ID,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_users],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["giftCard"] is None


QUERY_GIFT_CARD_EVENTS = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
            id
            events {
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
    }
"""


def test_query_gift_card_events(
    staff_api_client, app, gift_card, order, permission_manage_gift_card
):
    # given
    staff_user = staff_api_client.user
    parameters = {
        "message": "test message",
        "email": "testemail@email.com",
        "order_id": order.pk,
        "tag": "test tag",
        "old_tag": "test old tag",
        "balance": {
            "currency": "USD",
            "initial_balance": 10,
            "old_initial_balance": 20,
            "current_balance": 10,
            "old_current_balance": 5,
        },
        "expiry": {
            "expiry_type": GiftCardExpiryType.EXPIRY_PERIOD,
            "old_expiry_type": GiftCardExpiryType.EXPIRY_DATE,
            "expiry_period_type": TimePeriodType.MONTH,
            "expiry_period": 10,
            "expiry_date": datetime.date(2050, 1, 1),
        },
    }
    gift_card_events = GiftCardEvent.objects.bulk_create(
        [
            # gift card with empty fields
            GiftCardEvent(
                user=staff_user,
                gift_card=gift_card,
                type=GiftCardEvents.ISSUED,
                date=timezone.now(),
            ),
            # example gift card with all gift card event fields
            GiftCardEvent(
                user=staff_user,
                app=app,
                gift_card=gift_card,
                type=GiftCardEvents.UPDATED,
                parameters=parameters,
                date=timezone.now() + datetime.timedelta(days=10),
            ),
        ]
    )
    empty_event, full_event = gift_card_events

    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[permission_manage_gift_card],
    )

    # then
    content = get_graphql_content(response)
    events_data = content["data"]["giftCard"]["events"]
    assert len(events_data) == len(gift_card_events)

    assert events_data[0]["id"] == graphene.Node.to_global_id(
        "GiftCardEvent", empty_event.pk
    )
    assert events_data[0]["date"] == empty_event.date.isoformat()
    assert events_data[0]["type"] == empty_event.type.upper()
    assert events_data[0]["user"]["email"] == staff_user.email
    assert events_data[0]["app"] is None
    assert events_data[0]["message"] is None
    assert events_data[0]["email"] is None
    assert events_data[0]["orderId"] is None
    assert events_data[0]["orderNumber"] is None
    assert events_data[0]["tag"] is None
    assert events_data[0]["oldTag"] is None
    assert events_data[0]["balance"] is None
    assert events_data[0]["expiry"] is None

    assert events_data[1]["id"] == graphene.Node.to_global_id(
        "GiftCardEvent", full_event.pk
    )
    assert events_data[1]["date"] == full_event.date.isoformat()
    assert events_data[1]["type"] == full_event.type.upper()
    assert events_data[1]["user"]["email"] == staff_user.email
    assert events_data[1]["app"]["name"] == app.name
    assert events_data[1]["message"] == parameters["message"]
    assert events_data[1]["email"] == parameters["email"]
    assert events_data[1]["orderId"] == graphene.Node.to_global_id("Order", order.pk)
    assert events_data[1]["orderNumber"] == str(order.pk)
    assert events_data[1]["tag"] == parameters["tag"]
    assert events_data[1]["oldTag"] == parameters["old_tag"]
    assert (
        events_data[1]["balance"]["initialBalance"]["amount"]
        == parameters["balance"]["initial_balance"]
    )
    assert (
        events_data[1]["balance"]["initialBalance"]["currency"]
        == parameters["balance"]["currency"]
    )
    assert (
        events_data[1]["balance"]["oldInitialBalance"]["amount"]
        == parameters["balance"]["old_initial_balance"]
    )
    assert (
        events_data[1]["balance"]["oldInitialBalance"]["currency"]
        == parameters["balance"]["currency"]
    )
    assert (
        events_data[1]["balance"]["currentBalance"]["amount"]
        == parameters["balance"]["current_balance"]
    )
    assert (
        events_data[1]["balance"]["currentBalance"]["currency"]
        == parameters["balance"]["currency"]
    )
    assert (
        events_data[1]["balance"]["oldCurrentBalance"]["amount"]
        == parameters["balance"]["old_current_balance"]
    )
    assert (
        events_data[1]["balance"]["oldCurrentBalance"]["currency"]
        == parameters["balance"]["currency"]
    )
    assert (
        events_data[1]["expiry"]["expiryType"]
        == parameters["expiry"]["expiry_type"].upper()
    )
    assert (
        events_data[1]["expiry"]["oldExpiryType"]
        == parameters["expiry"]["old_expiry_type"].upper()
    )
    assert (
        events_data[1]["expiry"]["expiryDate"]
        == parameters["expiry"]["expiry_date"].isoformat()
    )
    assert events_data[1]["expiry"]["oldExpiryDate"] is None
    assert (
        events_data[1]["expiry"]["expiryPeriod"]["amount"]
        == parameters["expiry"]["expiry_period"]
    )
    assert (
        events_data[1]["expiry"]["expiryPeriod"]["type"]
        == parameters["expiry"]["expiry_period_type"].upper()
    )
    assert events_data[1]["expiry"]["oldExpiryPeriod"] is None
