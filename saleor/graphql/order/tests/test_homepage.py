from prices import Money

from ...core.enums import ReportingPeriod
from ...tests.utils import get_graphql_content


def test_homepage_events(order_events, staff_api_client, permission_manage_orders):
    query = """
    {
        homepageEvents(first: 20) {
            edges {
                node {
                    date
                    type
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    edges = content["data"]["homepageEvents"]["edges"]
    only_types = {"PLACED", "PLACED_FROM_DRAFT", "ORDER_FULLY_PAID"}
    assert {edge["node"]["type"] for edge in edges} == only_types


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
    permission_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_USD,
):
    # given
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross


def test_orders_total_channel_pln(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
    channel_PLN,
):
    # given
    order = order_with_lines_channel_PLN
    variables = {"period": ReportingPeriod.TODAY.name, "channel": channel_PLN.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, channel_PLN.currency_code) == order.total.gross


def test_orders_total_not_existing_channel(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    order_with_lines_channel_PLN,
):
    # given
    variables = {"period": ReportingPeriod.TODAY.name, "channel": "not-existing"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    assert not content["data"]["ordersTotal"]
