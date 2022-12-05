from datetime import date, timedelta
from decimal import Decimal

import graphene
import pytest
from freezegun import freeze_time

from .....core.postgres import FlatConcatSearchVector
from .....discount.models import OrderDiscount
from .....order import OrderStatus
from .....order.models import Order
from .....order.search import (
    prepare_order_search_vector_value,
    update_order_search_vector,
)
from ....tests.utils import get_graphql_content


@pytest.fixture
def draft_orders_query_with_filter():
    query = """
      query ($filter: OrderDraftFilterInput!, ) {
        draftOrders(first: 5, filter:$filter) {
          totalCount
          edges {
            node {
              id
            }
          }
        }
      }
    """
    return query


def test_draft_orders_query_with_filter_search_by_number(
    draft_orders_query_with_filter,
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": draft_order.number}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


def test_draft_orders_query_with_filter_search_by_number_with_hash(
    draft_orders_query_with_filter,
    draft_order,
    staff_api_client,
    permission_manage_orders,
):
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": f"#{draft_order.number}"}}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == 1


@pytest.mark.parametrize(
    "orders_filter, user_field, user_value",
    [
        ({"customer": "admin"}, "email", "admin@example.com"),
        ({"customer": "John"}, "first_name", "johnny"),
        ({"customer": "Snow"}, "last_name", "snow"),
    ],
)
def test_draft_order_query_with_filter_customer_fields(
    orders_filter,
    user_field,
    user_value,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(
        status=OrderStatus.DRAFT,
        user=customer_user,
        channel=channel_USD,
    )
    Order.objects.bulk_create(
        [
            order,
            Order(status=OrderStatus.DRAFT, channel=channel_USD),
        ]
    )

    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
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
        ({"created": {"gte": None}}, 2),
        ({"created": {"lte": None}}, 2),
    ],
)
def test_draft_order_query_with_filter_created_(
    orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    channel_USD,
):
    Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD)
    with freeze_time("2012-01-14"):
        Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD)
    variables = {"filter": orders_filter}
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]

    assert len(orders) == count


@pytest.mark.parametrize(
    "draft_orders_filter, count",
    [
        ({"search": "discount name"}, 2),
        ({"search": "Some other"}, 1),
        ({"search": "translated"}, 1),
        ({"search": "test@mirumee.com"}, 1),
        ({"search": "Leslie"}, 1),
        ({"search": "leslie wade"}, 1),
        ({"search": "Wade"}, 1),
        ({"search": ""}, 3),
    ],
)
def test_draft_orders_query_with_filter_search(
    draft_orders_filter,
    count,
    draft_orders_query_with_filter,
    staff_api_client,
    permission_manage_orders,
    customer_user,
    channel_USD,
):
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
            Order(
                user_email="user_email2@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
            ),
        ]
    )
    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal("1"),
                amount_value=Decimal("1"),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal("10"),
                amount_value=Decimal("10"),
                translated_name="PL_name",
            ),
        ]
    )
    for order in orders:
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )
    Order.objects.bulk_update(orders, ["search_vector"])

    variables = {"filter": draft_orders_filter}

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(draft_orders_query_with_filter, variables)
    content = get_graphql_content(response)
    assert content["data"]["draftOrders"]["totalCount"] == count
