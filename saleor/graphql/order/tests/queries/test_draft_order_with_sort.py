import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....order import OrderStatus
from .....order.models import Order
from ....tests.utils import get_graphql_content

QUERY_DRAFT_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        draftOrders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("draft_order_sort", "result_order"),
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2]),
        ({"field": "NUMBER", "direction": "DESC"}, [2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0, 2]),
    ],
)
def test_query_draft_orders_with_sort(
    draft_order_sort,
    result_order,
    staff_api_client,
    permission_group_manage_orders,
    address,
    channel_USD,
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                billing_address=address,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(10, "USD"), gross=Money(13, "USD")),
                channel=channel_USD,
            )
        )
    with freeze_time("2012-01-14"):
        address2 = address.get_copy()
        address2.first_name = "Walter"
        address2.save()
        created_orders.append(
            Order.objects.create(
                billing_address=address2,
                status=OrderStatus.DRAFT,
                total=TaxedMoney(net=Money(100, "USD"), gross=Money(130, "USD")),
                channel=channel_USD,
            )
        )
    address3 = address.get_copy()
    address3.last_name = "Alice"
    address3.save()
    created_orders.append(
        Order.objects.create(
            billing_address=address3,
            status=OrderStatus.DRAFT,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
            channel=channel_USD,
        )
    )
    variables = {"sort_by": draft_order_sort}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(QUERY_DRAFT_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    draft_orders = content["data"]["draftOrders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert draft_orders[order]["node"]["number"] == str(
            created_orders[order_number].number
        )
