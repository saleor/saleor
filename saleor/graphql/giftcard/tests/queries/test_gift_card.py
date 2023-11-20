import datetime
from copy import deepcopy

import graphene
import pytest
from django.utils import timezone

from .....giftcard import GiftCardEvents, events
from .....giftcard.models import GiftCardEvent
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import GiftCardEventsEnum

QUERY_GIFT_CARD_BY_ID = """
    query giftCard($id: ID!) {
        giftCard(id: $id){
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
    assert data["last4CodeChars"] == gift_card.display_code
    assert data["isActive"] == gift_card.is_active
    assert data["expiryDate"] is None
    assert data["tags"][0]["name"] == gift_card.tags.first().name
    assert data["created"] == gift_card.created_at.isoformat()
    assert data["lastUsedOn"] == gift_card.last_used_on
    assert data["boughtInChannel"] is None
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
    gift_card,
    non_shippable_gift_card_product,
    permission_manage_gift_card,
    permission_manage_users,
):
    # given
    query = QUERY_GIFT_CARD_BY_ID

    app = app_api_client.app
    gift_card.app = app
    gift_card.product = non_shippable_gift_card_product
    gift_card.save(update_fields=["app", "product"])

    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.pk)
    variables = {"id": gift_card_id}

    # when
    response = app_api_client.post_graphql(
        query,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    assert data["id"] == gift_card_id
    assert data["code"] == gift_card.code
    assert data["last4CodeChars"] == gift_card.display_code
    assert data["isActive"] == gift_card.is_active
    assert data["expiryDate"] is None
    assert data["tags"][0]["name"] == gift_card.tags.first().name
    assert data["created"] == gift_card.created_at.isoformat()
    assert data["lastUsedOn"] == gift_card.last_used_on
    assert data["initialBalance"]["currency"] == gift_card.initial_balance.currency
    assert data["initialBalance"]["amount"] == gift_card.initial_balance.amount
    assert data["currentBalance"]["currency"] == gift_card.current_balance.currency
    assert data["currentBalance"]["amount"] == gift_card.current_balance.amount
    assert data["createdBy"]["email"] == gift_card.created_by.email
    assert data["usedBy"] is None
    assert data["createdByEmail"] == gift_card.created_by_email
    assert data["usedByEmail"] == gift_card.used_by_email
    assert data["product"]["name"] == non_shippable_gift_card_product.name
    assert data["app"]["name"] == app.name


def test_query_gift_card_by_removed_app(
    staff_api_client,
    gift_card,
    removed_app,
    permission_manage_gift_card,
    permission_manage_users,
    permission_manage_apps,
):
    # given
    gift_card.app = removed_app
    gift_card.save(update_fields=["app"])
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
    assert data["last4CodeChars"] == gift_card_expiry_date.display_code
    assert data["expiryDate"] == gift_card_expiry_date.expiry_date.isoformat()


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
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: GiftCard."
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
    query giftCard($id: ID!, $filter: GiftCardEventFilterInput) {
        giftCard(id: $id){
            id
            boughtInChannel
            events(filter: $filter) {
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
        }
    }
"""


def test_query_gift_card_events(
    staff_api_client,
    app,
    gift_card,
    gift_card_event,
    order,
    permission_manage_gift_card,
    permission_manage_apps,
):
    # given
    staff_user = staff_api_client.user

    # gift card with empty fields
    empty_event = GiftCardEvent.objects.create(
        user=staff_user,
        gift_card=gift_card,
        type=GiftCardEvents.ISSUED,
        date=timezone.now(),
    )

    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    events_data = content["data"]["giftCard"]["events"]
    assert len(events_data) == gift_card.events.count()

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
    assert events_data[0]["tags"] is None
    assert events_data[0]["oldTags"] is None
    assert events_data[0]["balance"] is None
    assert events_data[0]["expiryDate"] is None

    assert events_data[1]["id"] == graphene.Node.to_global_id(
        "GiftCardEvent", gift_card_event.pk
    )
    assert events_data[1]["date"] == gift_card_event.date.isoformat()
    assert events_data[1]["type"] == gift_card_event.type.upper()
    assert events_data[1]["user"]["email"] == staff_user.email
    assert events_data[1]["app"]["name"] == app.name
    parameters = gift_card_event.parameters
    assert events_data[1]["message"] == parameters["message"]
    assert events_data[1]["email"] == parameters["email"]
    assert events_data[1]["orderId"] == graphene.Node.to_global_id("Order", order.pk)
    assert events_data[1]["orderNumber"] == str(order.number)
    assert events_data[1]["tags"] == parameters["tags"]
    assert events_data[1]["oldTags"] == parameters["old_tags"]
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
    assert events_data[1]["expiryDate"] == parameters["expiry_date"].isoformat()
    assert events_data[1]["oldExpiryDate"] == parameters["old_expiry_date"].isoformat()


def test_query_gift_card_event_with_removed_app(
    staff_api_client,
    removed_app,
    gift_card,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
):
    # given
    staff_api_client.user

    GiftCardEvent.objects.create(
        app=removed_app,
        gift_card=gift_card,
        type=GiftCardEvents.ISSUED,
        date=timezone.now(),
    )

    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    events_data = content["data"]["giftCard"]["events"]
    assert len(events_data) == 1
    assert events_data[0]["app"] is None


def test_query_gift_card_expiry_date_set_event(
    staff_api_client,
    gift_card,
    staff_user,
    permission_manage_gift_card,
    permission_manage_apps,
):
    # given
    old = deepcopy(gift_card)
    expiry_date = datetime.date(2050, 1, 1)
    gift_card.expiry_date = expiry_date
    gift_card.save(update_fields=["expiry_date"])

    events.gift_card_expiry_date_updated_event(gift_card, old, staff_user, None)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[permission_manage_gift_card, permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    events_data = content["data"]["giftCard"]["events"]
    assert len(events_data) == gift_card.events.count()
    event_data = events_data[0]
    assert event_data["expiryDate"] == expiry_date.isoformat()
    assert event_data["oldExpiryDate"] is None
    assert event_data["user"]["email"] == staff_user.email
    assert event_data["app"] is None
    assert event_data["type"] == GiftCardEvents.EXPIRY_DATE_UPDATED.upper()
    assert event_data["balance"] is None


def test_query_gift_card_used_in_order_event(
    staff_api_client,
    gift_card,
    app,
    order,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
):
    # given
    previous_balance = 10.0
    balance_data = [(gift_card, previous_balance)]
    events.gift_cards_used_in_order_event(balance_data, order, None, app)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    events_data = content["data"]["giftCard"]["events"]
    assert len(events_data) == gift_card.events.count()
    event_data = events_data[0]
    assert (
        event_data["balance"]["currentBalance"]["amount"]
        == gift_card.current_balance_amount
    )
    assert event_data["balance"]["currentBalance"]["currency"] == gift_card.currency
    assert event_data["balance"]["oldCurrentBalance"]["amount"] == previous_balance
    assert event_data["balance"]["oldCurrentBalance"]["currency"] == gift_card.currency
    assert event_data["expiryDate"] is None
    assert events_data[0]["user"] is None
    assert events_data[0]["app"]["name"] == app.name
    assert event_data["type"] == GiftCardEvents.USED_IN_ORDER.upper()


def test_query_gift_card_bought_event(
    staff_api_client,
    gift_card_expiry_date,
    order,
    app,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
):
    # given
    events.gift_cards_bought_event([gift_card_expiry_date], order, None, app)
    variables = {"id": graphene.Node.to_global_id("GiftCard", gift_card_expiry_date.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    events_data = data["events"]
    assert data["boughtInChannel"] == order.channel.slug
    assert len(events_data) == gift_card_expiry_date.events.count()
    event_data = events_data[0]
    assert event_data["balance"] is None
    assert event_data["expiryDate"] == gift_card_expiry_date.expiry_date.isoformat()
    assert event_data["orderId"] == graphene.Node.to_global_id("Order", order.id)
    assert event_data["type"] == GiftCardEvents.BOUGHT.upper()
    assert event_data["user"] is None
    assert event_data["app"]["name"] == app.name


@pytest.mark.parametrize(
    ("gift_card_type", "count"),
    [
        (GiftCardEventsEnum.BOUGHT.name, 1),
        (GiftCardEventsEnum.USED_IN_ORDER.name, 2),
        ((GiftCardEventsEnum.ISSUED.name, 0)),
    ],
)
def test_query_gift_card_events_filter_by_type(
    gift_card_type,
    count,
    staff_api_client,
    gift_card_expiry_date,
    gift_card,
    order,
    app,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
):
    # given
    previous_balance = 10.0
    balance_data = [(gift_card, previous_balance)]
    events.gift_cards_bought_event([gift_card, gift_card_expiry_date], order, None, app)
    events.gift_cards_used_in_order_event(balance_data, order, None, app)
    events.gift_cards_used_in_order_event(balance_data, order, None, app)

    assert gift_card.events.count() == 3
    assert GiftCardEvent.objects.count() == 4

    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "filter": {
            "type": gift_card_type,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    events_data = data["events"]
    assert len(events_data) == count
    for event_data in events_data:
        assert event_data["type"] == gift_card_type


def test_query_gift_card_events_filter_by_orders(
    staff_api_client,
    gift_card_expiry_date,
    gift_card,
    app,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
    order_list,
):
    # given
    previous_balance = 10.0
    events.gift_cards_bought_event(
        [gift_card, gift_card_expiry_date], order_list[0], None, app
    )
    balance_data = [(gift_card, previous_balance)]
    events.gift_cards_used_in_order_event(balance_data, order_list[1], None, app)
    events.gift_cards_used_in_order_event(balance_data, order_list[2], None, app)

    assert gift_card.events.count() == 3
    assert GiftCardEvent.objects.count() == 4

    order_ids = [
        graphene.Node.to_global_id("Order", order.pk) for order in order_list[:2]
    ]
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "filter": {
            "orders": order_ids,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    events_data = data["events"]
    assert len(events_data) == 2
    assert {event["orderId"] for event in events_data} == set(order_ids)
    assert {event["type"] for event in events_data} == {
        GiftCardEvents.USED_IN_ORDER.upper(),
        GiftCardEvents.BOUGHT.upper(),
    }


def test_query_gift_card_events_filter_by_orders_no_events(
    staff_api_client,
    gift_card_expiry_date,
    gift_card,
    order,
    app,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_users,
):
    # given
    previous_balance = 10.0
    balance_data = [(gift_card, previous_balance)]
    events.gift_cards_bought_event([gift_card, gift_card_expiry_date], order, None, app)
    events.gift_cards_used_in_order_event(balance_data, order, None, app)

    assert gift_card.events.count() == 2
    assert GiftCardEvent.objects.count() == 3

    order_id = graphene.Node.to_global_id("Order", 2)
    variables = {
        "id": graphene.Node.to_global_id("GiftCard", gift_card.pk),
        "filter": {
            "orders": [order_id],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_GIFT_CARD_EVENTS,
        variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_users,
        ],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["giftCard"]
    events_data = data["events"]
    assert not events_data
