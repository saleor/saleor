import warnings

from prices import Money

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....core.enums import ReportingPeriod
from ....tests.utils import get_graphql_content

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


def test_orders_total(staff_api_client, permission_manage_orders, order_with_lines):
    # given
    order = order_with_lines
    variables = {"period": ReportingPeriod.TODAY.name}

    # when
    with warnings.catch_warnings(record=True) as warns:
        response = staff_api_client.post_graphql(
            QUERY_ORDER_TOTAL, variables, permissions=[permission_manage_orders]
        )
        content = get_graphql_content(response)

    # then
    amount = str(content["data"]["ordersTotal"]["gross"]["amount"])
    assert Money(amount, "USD") == order.total.gross
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
