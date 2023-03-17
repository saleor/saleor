from datetime import date, timedelta

import pytest
from prices import Money

from ....order import OrderEvents
from ....order.models import Order, OrderEvent
from ...core.enums import ReportingPeriod
from ...tests.utils import assert_no_permission, get_graphql_content

QUERY_HOMEPAGE_EVENTS = """
{
    homepageEvents(first: 20) {
        edges {
            node {
                date
                type
                orderNumber
            }
        }
    }
}
"""


@pytest.fixture
def order_events_from_different_channels(
    order_events,
    order_list,
    channel_PLN,
    channel_JPY,
    channel_USD,
):
    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    events = list(
        OrderEvent.objects.filter(
            type__in=[
                OrderEvents.PLACED,
                OrderEvents.PLACED_FROM_DRAFT,
                OrderEvents.ORDER_FULLY_PAID,
            ]
        )
    )

    events[0].order = order_list[0]
    events[1].order = order_list[1]
    events[2].order = order_list[2]
    OrderEvent.objects.bulk_update(events, ["order"])

    return order_events


def test_homepage_events(
    order_events_from_different_channels,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    query = QUERY_HOMEPAGE_EVENTS
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(query)

    # when
    content = get_graphql_content(response)

    # then
    edges = content["data"]["homepageEvents"]["edges"]
    only_types = {"PLACED", "PLACED_FROM_DRAFT", "ORDER_FULLY_PAID"}
    assert {edge["node"]["type"] for edge in edges} == only_types
    expected_numbers = set(
        OrderEvent.objects.filter(
            type__in=[
                OrderEvents.PLACED,
                OrderEvents.PLACED_FROM_DRAFT,
                OrderEvents.ORDER_FULLY_PAID,
            ]
        ).values_list("order__number", flat=True)
    )
    assert {int(edge["node"]["orderNumber"]) for edge in edges} == expected_numbers


def test_query_homepage_events_by_user_with_restricted_access_to_channels(
    order_events_from_different_channels,
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    channel_USD,
):
    # given
    user = staff_api_client.user
    permission_group_all_perms_channel_USD_only.user_set.add(user)

    # when
    response = staff_api_client.post_graphql(QUERY_HOMEPAGE_EVENTS)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["homepageEvents"]["edges"]) == 1
    event = OrderEvent.objects.filter(
        type__in=[
            OrderEvents.PLACED,
            OrderEvents.PLACED_FROM_DRAFT,
            OrderEvents.ORDER_FULLY_PAID,
        ],
        order__channel=channel_USD,
    ).first()
    assert content["data"]["homepageEvents"]["edges"][0]["node"]["orderNumber"] == str(
        event.order.number
    )


def test_query_homepage_by_user_with_restricted_access_to_channels_no_acc_channels(
    order_events_from_different_channels,
    staff_api_client,
    permission_group_all_perms_without_any_channel,
):
    """Ensure that query returns no orders when user has no accessible channels."""
    # given
    user = staff_api_client.user
    permission_group_all_perms_without_any_channel.user_set.add(user)

    # when
    response = staff_api_client.post_graphql(QUERY_HOMEPAGE_EVENTS)
    content = get_graphql_content(response)

    # then
    assert len(content["data"]["homepageEvents"]["edges"]) == 0


def test_query_homepage_by_app(
    order_events_from_different_channels,
    app_api_client,
    permission_manage_orders,
):
    # when
    response = app_api_client.post_graphql(
        QUERY_HOMEPAGE_EVENTS, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    events = OrderEvent.objects.filter(
        type__in=[
            OrderEvents.PLACED,
            OrderEvents.PLACED_FROM_DRAFT,
            OrderEvents.ORDER_FULLY_PAID,
        ]
    )
    assert len(content["data"]["homepageEvents"]["edges"]) == events.count()


def test_query_homepage_by_customer(
    order_events_from_different_channels,
    order_list,
    user_api_client,
):
    # when
    response = user_api_client.post_graphql(QUERY_HOMEPAGE_EVENTS)

    # then
    assert_no_permission(response)


QUERY_ORDER_TOTAL = """
query Orders($period: ReportingPeriod, $channel: String) {
    ordersTotal(period: $period, channel: $channel ) {
        gross {
            amount
            currency
        }
        net {
            currency
            amount
        }
    }
}
"""


def test_orders_total(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross


def test_orders_total_channel_pln(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines_channel_PLN
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, channel_PLN.currency_code) == order.total.gross


def test_orders_total_not_existing_channel(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"period": ReportingPeriod.TODAY.name, "channel": "not-existing"}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    content = get_graphql_content(response)
    assert not content["data"]["ordersTotal"]


def test_orders_total_as_staff(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross


def test_orders_total_no_access_to_channel(
    staff_api_client, permission_group_all_perms_channel_USD_only, orders, channel_JPY
):
    # given
    query = QUERY_ORDER_TOTAL

    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_JPY.slug}

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    assert_no_permission(response)


def test_orders_total_as_app(
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross


def test_orders_total_as_customer(
    user_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    assert_no_permission(response)


def test_orders_total_as_anonymous(
    api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(QUERY_ORDER_TOTAL, variables)

    # then
    assert_no_permission(response)


QUERY_ORDER_TODAY_COUNT = """
    query OrdersToday($created: DateRangeInput, $channel: String) {
        orders(filter: {created: $created}, channel: $channel ) {
            totalCount
        }
    }
"""


def test_orders_total_count_without_channel(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        }
    }

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 2


def test_orders_total_count_channel_USD(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_total_count_channel_PLN(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_PLN.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_total_count_as_staff(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_total_count_as_app(
    app_api_client,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = app_api_client.post_graphql(
        QUERY_ORDER_TODAY_COUNT, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


def test_orders_total_count_as_customer(
    user_api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = user_api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    assert_no_permission(response)


def test_orders_total_count_as_anonymous(
    api_client,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    variables = {
        "created": {
            "gte": str(date.today() - timedelta(days=3)),
            "lte": str(date.today()),
        },
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_ORDER_TODAY_COUNT, variables)

    # then
    assert_no_permission(response)
