import uuid
from datetime import date, timedelta

import graphene
import pytest
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ....order.models import Order, OrderStatus
from ....payment import ChargeStatus
from ...tests.utils import get_graphql_content


@pytest.fixture()
def orders_for_pagination(db, channel_USD):
    orders = Order.objects.bulk_create(
        [
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(1, "USD"), gross=Money(1, "USD")),
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(2, "USD"), gross=Money(2, "USD")),
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(3, "USD"), gross=Money(3, "USD")),
                channel=channel_USD,
            ),
        ]
    )
    return orders


@pytest.fixture()
def draft_orders_for_pagination(db, channel_USD):
    orders = Order.objects.bulk_create(
        [
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(1, "USD"), gross=Money(1, "USD")),
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(2, "USD"), gross=Money(2, "USD")),
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                total=TaxedMoney(net=Money(3, "USD"), gross=Money(3, "USD")),
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
        ]
    )
    return orders


QUERY_ORDERS_WITH_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: OrderSortingInput, $filter: OrderFilterInput
    ){
        orders(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            totalCount
            edges {
                node {
                    id
                    number
                    total{
                        gross{
                            amount
                        }
                    }
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""

QUERY_DRAFT_ORDERS_WITH_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: OrderSortingInput, $filter: OrderDraftFilterInput
    ){
        draftOrders(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            totalCount
            edges {
                node {
                    id
                    number
                    total{
                        gross{
                            amount
                        }
                    }
                    created
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.mark.parametrize(
    "orders_filter, orders_order, expected_total_count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            [3.0, 2.0],
            3,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, [3.0, 2.0], 3),
        ({"created": {"lte": str(date.today())}}, [0.0, 3.0], 4),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, [0.0], 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, [], 0),
    ],
)
def test_order_query_pagination_with_filter_created(
    orders_filter,
    orders_order,
    expected_total_count,
    staff_api_client,
    permission_manage_orders,
    orders_for_pagination,
    channel_USD,
):
    with freeze_time("2012-01-14"):
        Order.objects.create(channel=channel_USD)
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)

    orders = content["data"]["orders"]["edges"]
    total_count = content["data"]["orders"]["totalCount"]

    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]

    assert expected_total_count == total_count


@pytest.mark.parametrize(
    "orders_filter, expected_total_count, payment_status, orders_order",
    [
        ({"paymentStatus": "FULLY_CHARGED"}, 1, ChargeStatus.FULLY_CHARGED, [98.4]),
        ({"paymentStatus": "NOT_CHARGED"}, 4, ChargeStatus.NOT_CHARGED, [3.0, 2.0]),
        (
            {"paymentStatus": "PARTIALLY_CHARGED"},
            1,
            ChargeStatus.PARTIALLY_CHARGED,
            [98.4],
        ),
        (
            {"paymentStatus": "PARTIALLY_REFUNDED"},
            1,
            ChargeStatus.PARTIALLY_REFUNDED,
            [98.4],
        ),
        ({"paymentStatus": "FULLY_REFUNDED"}, 1, ChargeStatus.FULLY_REFUNDED, [98.4]),
        ({"paymentStatus": "FULLY_CHARGED"}, 0, ChargeStatus.FULLY_REFUNDED, []),
        ({"paymentStatus": "NOT_CHARGED"}, 3, ChargeStatus.FULLY_REFUNDED, [3.0, 2.0]),
    ],
)
def test_order_query_pagination_with_filter_payment_status(
    orders_filter,
    expected_total_count,
    payment_status,
    orders_order,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
    orders_for_pagination,
):
    payment_dummy.charge_status = payment_status
    payment_dummy.save()

    for order in orders_for_pagination:
        payment_dummy.id = None
        payment_dummy.order = order
        payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
        payment_dummy.save()

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)

    orders = content["data"]["orders"]["edges"]
    total_count = content["data"]["orders"]["totalCount"]
    assert total_count == expected_total_count

    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]


@pytest.mark.parametrize(
    "orders_filter, expected_total_count, status, orders_order",
    [
        ({"status": "UNFULFILLED"}, 4, OrderStatus.UNFULFILLED, [3.0, 2.0]),
        ({"status": "PARTIALLY_FULFILLED"}, 1, OrderStatus.PARTIALLY_FULFILLED, [0.0]),
        ({"status": "FULFILLED"}, 1, OrderStatus.FULFILLED, [0.0]),
        ({"status": "CANCELED"}, 1, OrderStatus.CANCELED, [0.0]),
    ],
)
def test_order_query_pagination_with_filter_status(
    orders_filter,
    expected_total_count,
    status,
    orders_order,
    staff_api_client,
    permission_manage_orders,
    order,
    orders_for_pagination,
):
    order.status = status
    order.save()

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)

    orders = content["data"]["orders"]["edges"]
    total_count = content["data"]["orders"]["totalCount"]
    assert total_count == expected_total_count

    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_order_query_pagination_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    orders_for_pagination,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order.objects.create(
        user=customer_user, token=str(uuid.uuid4()), channel=channel_USD
    )

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_draft_order_query_pagination_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    draft_orders_for_pagination,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order.objects.create(
        status=OrderStatus.DRAFT,
        user=customer_user,
        token=str(uuid.uuid4()),
        channel=channel_USD,
    )

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_PAGINATION, variables
    )
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    "orders_filter, expected_total_count, orders_order",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            3,
            [3.0, 2.0],
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 3, [3.0, 2.0]),
        ({"created": {"lte": str(date.today())}}, 4, [0.0, 3.0]),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1, [0.0]),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0, []),
    ],
)
def test_draft_order_query_pagination_with_filter_created(
    orders_filter,
    expected_total_count,
    orders_order,
    staff_api_client,
    permission_manage_orders,
    draft_orders_for_pagination,
    channel_USD,
):
    with freeze_time("2012-01-14"):
        Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD)
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_PAGINATION, variables
    )
    content = get_graphql_content(response)

    orders = content["data"]["draftOrders"]["edges"]
    total_count = content["data"]["draftOrders"]["totalCount"]

    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]

    assert expected_total_count == total_count


@pytest.mark.parametrize(
    "orders_filter, expected_total_count, orders_order",
    [
        ({"search": "test_discount"}, 2, [0.0, 0.0]),
        ({"search": "test_discount1"}, 1, [0.0]),
        ({"search": "translated_discount1_name"}, 1, [0.0]),
        ({"search": "user"}, 2, [0.0, 0.0]),
        ({"search": "user1@example.com"}, 1, [0.0]),
        ({"search": "test@example.com"}, 1, [0.0]),
        ({"search": "Leslie"}, 1, [0.0]),
        ({"search": "Wade"}, 1, [0.0]),
        ({"search": ""}, 6, [0.0, 0.0]),
    ],
)
def test_orders_query_pagination_with_filter_search(
    orders_filter,
    expected_total_count,
    orders_order,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    orders_for_pagination,
    channel_USD,
):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                discount_name="test_discount1",
                user_email="test@example.com",
                translated_discount_name="translated_discount1_name",
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user1@example.com",
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
                channel=channel_USD,
            ),
        ]
    )
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)

    orders = content["data"]["orders"]["edges"]
    total_count = content["data"]["orders"]["totalCount"]

    assert expected_total_count == total_count
    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]


def test_orders_query_pagination_with_filter_search_by_id(
    order, staff_api_client, permission_manage_orders
):
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": {"search": order.pk}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "draft_orders_filter, expected_total_count, orders_order",
    [
        ({"search": "test_discount"}, 2, [0.0, 0.0]),
        ({"search": "test_discount1"}, 1, [0.0]),
        ({"search": "translated_discount1_name"}, 1, [0.0]),
        ({"search": "user"}, 2, [0.0, 0.0]),
        ({"search": "user1@example.com"}, 1, [0.0]),
        ({"search": "test@example.com"}, 1, [0.0]),
        ({"search": "Leslie"}, 1, [0.0]),
        ({"search": "Wade"}, 1, [0.0]),
        ({"search": ""}, 6, [0.0, 0.0]),
    ],
)
def test_draft_orders_query_pagination_with_filter_search(
    draft_orders_filter,
    expected_total_count,
    orders_order,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    draft_orders_for_pagination,
    channel_USD,
):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                discount_name="test_discount1",
                user_email="test@example.com",
                translated_discount_name="translated_discount1_name",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user1@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
        ]
    )
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": draft_orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_PAGINATION, variables
    )
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    total_count = content["data"]["draftOrders"]["totalCount"]

    assert expected_total_count == total_count
    for i in range(total_count if total_count < page_size else page_size):
        assert orders[i]["node"]["total"]["gross"]["amount"] == orders_order[i]


def test_draft_orders_query_pagination_with_filter_search_by_id(
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    page_size = 2
    variables = {
        "first": page_size,
        "after": None,
        "filter": {"search": draft_order.pk},
    }
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_PAGINATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "order_sort, result_order",
    [
        ({"field": "NUMBER", "direction": "ASC"}, [0, 1]),
        ({"field": "NUMBER", "direction": "DESC"}, [2, 1]),
        ({"field": "CREATION_DATE", "direction": "ASC"}, [1, 0]),
        ({"field": "CREATION_DATE", "direction": "DESC"}, [2, 0]),
        ({"field": "CUSTOMER", "direction": "ASC"}, [2, 0]),
        ({"field": "CUSTOMER", "direction": "DESC"}, [1, 0]),
        ({"field": "FULFILLMENT_STATUS", "direction": "ASC"}, [2, 1]),
        ({"field": "FULFILLMENT_STATUS", "direction": "DESC"}, [0, 1]),
    ],
)
def test_query_orders_pagination_with_sort(
    order_sort,
    result_order,
    staff_api_client,
    permission_manage_orders,
    address,
    channel_USD,
):
    created_orders = []
    with freeze_time("2017-01-14"):
        created_orders.append(
            Order.objects.create(
                token=str(uuid.uuid4()),
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
                token=str(uuid.uuid4()),
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
            token=str(uuid.uuid4()),
            billing_address=address3,
            status=OrderStatus.CANCELED,
            total=TaxedMoney(net=Money(20, "USD"), gross=Money(26, "USD")),
            channel=channel_USD,
        )
    )
    page_size = 2
    variables = {"first": page_size, "after": None, "sortBy": order_sort}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    for order, order_number in enumerate(result_order):
        assert orders[order]["node"]["number"] == str(created_orders[order_number].pk)
