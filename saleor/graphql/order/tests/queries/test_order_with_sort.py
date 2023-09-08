import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....order import OrderStatus
from .....order.models import Order
from ....tests.utils import get_graphql_content

QUERY_ORDER_WITH_SORT = """
    query ($sort_by: OrderSortingInput!) {
        orders(first:5, sortBy: $sort_by) {
            edges{
                node{
                    number
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1, 2, 3]),
        ({"field": "NUMBER", "direction": "DESC"}, [3, 2, 1, 0]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0, 2, 3]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [3, 2, 0, 1]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0, 1, 3]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [3, 1, 0, 2]),
        ({"field": "FULFILLMENT_STATUS", "direction": "ASC"}, [2, 1, 0, 3]),
        ({"field": "FULFILLMENT_STATUS", "direction": "DESC"}, [3, 0, 1, 2]),
    ],
)
def test_query_orders_with_sort(
    order_sort,
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
                status=OrderStatus.PARTIALLY_FULFILLED,
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
                status=OrderStatus.FULFILLED,
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
            status=OrderStatus.CANCELED,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
            channel=channel_USD,
        )
    )
    created_orders.append(
        Order.objects.create(
            billing_address=None,
            status=OrderStatus.UNCONFIRMED,
            total=TaxedMoney(net=Money(60, "USD"), gross=Money(80, "USD")),
            channel=channel_USD,
        )
    )
    variables = {"sort_by": order_sort}
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    response = staff_api_client.post_graphql(QUERY_ORDER_WITH_SORT, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert orders[order]["node"]["number"] == str(
            created_orders[order_number].number
        )


SEARCH_ORDERS_QUERY = """
    query Orders(
        $filters: OrderFilterInput,
        $sortBy: OrderSortingInput,
        $after: String,
    ) {
        orders(
            first: 5,
            filter: $filters,
            sortBy: $sortBy,
            after: $after,
        ) {
            edges {
                node {
                    id
                }
                cursor
            }
        }
    }
"""


def test_sort_order_by_rank_without_search(
    staff_api_client, permission_group_manage_orders
):
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "sortBy": {"field": "RANK", "direction": "DESC"},
    }
    response = staff_api_client.post_graphql(SEARCH_ORDERS_QUERY, variables)
    content = get_graphql_content(response, ignore_errors=True)

    assert "errors" in content
    assert (
        content["errors"][0]["message"]
        == "Sorting by RANK is available only when using a search filter."
    )


def test_sort_order_by_rank_with_nonetype_search(
    staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "sortBy": {"field": "RANK", "direction": "DESC"},
        "search": None,
    }

    # when
    response = staff_api_client.post_graphql(SEARCH_ORDERS_QUERY, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)

    errors = content["errors"]
    expected_message = "Sorting by RANK is available only when using a search filter."
    assert len(errors) == 1
    assert errors[0]["message"] == expected_message
