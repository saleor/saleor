import uuid
from datetime import date, timedelta

import graphene
import pytest
from freezegun import freeze_time

from saleor.order.models import Order, OrderStatus
from saleor.payment import ChargeStatus

from ..utils import get_graphql_content

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
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_order_query_pagination_with_filter_created(
    orders_filter, count, staff_api_client, permission_manage_orders,
):
    Order.objects.create()
    with freeze_time("2012-01-14"):
        Order.objects.create()
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, payment_status",
    [
        ({"paymentStatus": "FULLY_CHARGED"}, 1, ChargeStatus.FULLY_CHARGED),
        ({"paymentStatus": "NOT_CHARGED"}, 2, ChargeStatus.NOT_CHARGED),
        ({"paymentStatus": "PARTIALLY_CHARGED"}, 1, ChargeStatus.PARTIALLY_CHARGED),
        ({"paymentStatus": "PARTIALLY_REFUNDED"}, 1, ChargeStatus.PARTIALLY_REFUNDED),
        ({"paymentStatus": "FULLY_REFUNDED"}, 1, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "FULLY_CHARGED"}, 0, ChargeStatus.FULLY_REFUNDED),
        ({"paymentStatus": "NOT_CHARGED"}, 1, ChargeStatus.FULLY_REFUNDED),
    ],
)
def test_order_query_pagination_with_filter_payment_status(
    orders_filter,
    count,
    payment_status,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
):
    payment_dummy.charge_status = payment_status
    payment_dummy.save()

    payment_dummy.id = None
    payment_dummy.order = Order.objects.create()
    payment_dummy.charge_status = ChargeStatus.NOT_CHARGED
    payment_dummy.save()

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count, status",
    [
        ({"status": "UNFULFILLED"}, 2, OrderStatus.UNFULFILLED),
        ({"status": "PARTIALLY_FULFILLED"}, 1, OrderStatus.PARTIALLY_FULFILLED),
        ({"status": "FULFILLED"}, 1, OrderStatus.FULFILLED),
        ({"status": "CANCELED"}, 1, OrderStatus.CANCELED),
    ],
)
def test_order_query_pagination_with_filter_status(
    orders_filter,
    count,
    status,
    staff_api_client,
    payment_dummy,
    permission_manage_orders,
    order,
):
    order.status = status
    order.save()

    Order.objects.create()

    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)

    orders_ids_from_response = [o["node"]["id"] for o in orders]
    assert len(orders) == count
    assert order_id in orders_ids_from_response


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
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(user=customer_user, token=str(uuid.uuid4()))
    Order.objects.bulk_create([order, Order(token=str(uuid.uuid4()))])

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
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(status=OrderStatus.DRAFT, user=customer_user, token=str(uuid.uuid4()))
    Order.objects.bulk_create(
        [order, Order(token=str(uuid.uuid4()), status=OrderStatus.DRAFT)]
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
    "orders_filter, count",
    [
        (
            {
                "created": {
                    "gte": str(date.today() - timedelta(days=3)),
                    "lte": str(date.today()),
                }
            },
            1,
        ),
        ({"created": {"gte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"lte": str(date.today())}}, 2),
        ({"created": {"lte": str(date.today() - timedelta(days=3))}}, 1),
        ({"created": {"gte": str(date.today() + timedelta(days=1))}}, 0),
    ],
)
def test_draft_order_query_pagination_with_filter_created(
    orders_filter, count, staff_api_client, permission_manage_orders,
):
    Order.objects.create(status=OrderStatus.DRAFT)
    with freeze_time("2012-01-14"):
        Order.objects.create(status=OrderStatus.DRAFT)
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(
        QUERY_DRAFT_ORDERS_WITH_PAGINATION, variables
    )
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "orders_filter, count",
    [
        ({"search": "test_discount"}, 2),
        ({"search": "test_discount1"}, 1),
        ({"search": "translated_discount1_name"}, 1),
        ({"search": "user"}, 2),
        ({"search": "user1@example.com"}, 1),
        ({"search": "test@example.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_orders_query_pagination_with_filter_search(
    orders_filter, count, staff_api_client, permission_manage_orders, customer_user,
):
    Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                token=str(uuid.uuid4()),
                discount_name="test_discount1",
                user_email="test@example.com",
                translated_discount_name="translated_discount1_name",
            ),
            Order(token=str(uuid.uuid4()), user_email="user1@example.com"),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
            ),
        ]
    )
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(QUERY_ORDERS_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["orders"]["totalCount"] == count


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
    "draft_orders_filter, count",
    [
        ({"search": "test_discount"}, 2),
        ({"search": "test_discount1"}, 1),
        ({"search": "translated_discount1_name"}, 1),
        ({"search": "user"}, 2),
        ({"search": "user1@example.com"}, 1),
        ({"search": "test@example.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_draft_orders_query_pagination_with_filter_search(
    draft_orders_filter,
    count,
    staff_api_client,
    permission_manage_orders,
    customer_user,
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
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user1@example.com",
                status=OrderStatus.DRAFT,
            ),
            Order(
                token=str(uuid.uuid4()),
                user_email="user2@example.com",
                discount_name="test_discount2",
                translated_discount_name="translated_discount2_name",
                status=OrderStatus.DRAFT,
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
    assert content["data"]["draftOrders"]["totalCount"] == count


def test_draft_orders_query_pagination_with_filter_search_by_id(
    draft_order, staff_api_client, permission_manage_orders,
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
