import datetime
from decimal import Decimal

import graphene
import pytest
from django.core.exceptions import ValidationError
from freezegun import freeze_time

from .....core.postgres import FlatConcatSearchVector
from .....discount.models import OrderDiscount
from .....order import OrderStatus
from .....order.models import Order
from .....order.search import (
    prepare_order_search_vector_value,
    update_order_search_vector,
)
from ....core.connection import where_filter_qs
from ....tests.utils import get_graphql_content
from ...filters import OrderDiscountedObjectWhere

DRAFT_ORDERS_QUERY_WITH_FILTER = """
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


def test_draft_orders_query_with_filter_search_by_number(
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": draft_order.number}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_QUERY_WITH_FILTER, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["draftOrders"]["totalCount"] == 1


def test_draft_orders_query_with_filter_search_by_number_with_hash(
    draft_order,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    update_order_search_vector(draft_order)
    variables = {"filter": {"search": f"#{draft_order.number}"}}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_QUERY_WITH_FILTER, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["draftOrders"]["totalCount"] == 1


@pytest.mark.parametrize(
    ("orders_filter", "user_field", "user_value"),
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
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    channel_USD,
):
    # given
    setattr(customer_user, user_field, user_value)
    customer_user.save()
    customer_user.refresh_from_db()

    order = Order(
        status=OrderStatus.DRAFT,
        user=customer_user,
        channel=channel_USD,
        lines_count=0,
    )
    Order.objects.bulk_create(
        [
            order,
            Order(status=OrderStatus.DRAFT, channel=channel_USD, lines_count=0),
        ]
    )

    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_QUERY_WITH_FILTER, variables)
    content = get_graphql_content(response)

    # then
    orders = content["data"]["draftOrders"]["edges"]
    order_id = graphene.Node.to_global_id("Order", order.pk)
    assert len(orders) == 1
    assert orders[0]["node"]["id"] == order_id


@pytest.mark.parametrize(
    ("orders_filter", "count"),
    [
        (
            {
                "created": {
                    "gte": str(
                        datetime.datetime.now(tz=datetime.UTC).date()
                        - datetime.timedelta(days=3)
                    ),
                    "lte": str(datetime.datetime.now(tz=datetime.UTC).date()),
                }
            },
            1,
        ),
        (
            {
                "created": {
                    "gte": str(
                        datetime.datetime.now(tz=datetime.UTC).date()
                        - datetime.timedelta(days=3)
                    )
                }
            },
            1,
        ),
        ({"created": {"lte": str(datetime.datetime.now(tz=datetime.UTC).date())}}, 2),
        (
            {
                "created": {
                    "lte": str(
                        datetime.datetime.now(tz=datetime.UTC).date()
                        - datetime.timedelta(days=3)
                    )
                }
            },
            1,
        ),
        (
            {
                "created": {
                    "gte": str(
                        datetime.datetime.now(tz=datetime.UTC).date()
                        + datetime.timedelta(days=1)
                    )
                }
            },
            0,
        ),
        ({"created": {"gte": None}}, 2),
        ({"created": {"lte": None}}, 2),
    ],
)
def test_draft_order_query_with_filter_created(
    orders_filter,
    count,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    Order.objects.create(status=OrderStatus.DRAFT, channel=channel_USD, lines_count=0)
    with freeze_time("2012-01-14"):
        Order.objects.create(
            status=OrderStatus.DRAFT, channel=channel_USD, lines_count=0
        )
    variables = {"filter": orders_filter}
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_QUERY_WITH_FILTER, variables)
    content = get_graphql_content(response)

    # then
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == count


@pytest.mark.parametrize(
    ("draft_orders_filter", "count"),
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
    staff_api_client,
    permission_group_manage_orders,
    customer_user,
    channel_USD,
):
    # given
    orders = Order.objects.bulk_create(
        [
            Order(
                user=customer_user,
                user_email="test@mirumee.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
                lines_count=0,
            ),
            Order(
                user_email="user_email1@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
                lines_count=0,
            ),
            Order(
                user_email="user_email2@example.com",
                status=OrderStatus.DRAFT,
                channel=channel_USD,
                lines_count=0,
            ),
        ]
    )
    OrderDiscount.objects.bulk_create(
        [
            OrderDiscount(
                order=orders[0],
                name="Some discount name",
                value=Decimal(1),
                amount_value=Decimal(1),
                translated_name="translated",
            ),
            OrderDiscount(
                order=orders[2],
                name="Some other discount name",
                value=Decimal(10),
                amount_value=Decimal(10),
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
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_QUERY_WITH_FILTER, variables)
    content = get_graphql_content(response)

    # then
    assert content["data"]["draftOrders"]["totalCount"] == count


@pytest.mark.parametrize(("gte", "count"), [(20, 1), (0, 1), (500, 0), (20.01, 0)])
def test_draft_orders_query_with_filter_base_total_price_range(draft_order, gte, count):
    # given
    order = draft_order
    currency = order.currency
    order.total_net_amount = Decimal(20)
    order.save(update_fields=["total_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "currency": currency,
        "base_total_price": {
            "range": {
                "gte": gte,
            }
        },
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        OrderDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == count
    if count:
        assert result.first() == order


@pytest.mark.parametrize(("gte", "count"), [(20, 1), (0, 1), (500, 0), (20.01, 0)])
def test_draft_orders_query_with_filter_base_subtotal_price_range(
    draft_order, gte, count
):
    # given
    order = draft_order
    currency = order.currency
    order.subtotal_net_amount = Decimal(20)
    order.save(update_fields=["subtotal_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "currency": currency,
        "base_subtotal_price": {
            "range": {
                "gte": gte,
            }
        },
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        OrderDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == count
    if count:
        assert result.first() == order


@pytest.mark.parametrize(
    ("one_of", "count"), [([1, 20, 70], 1), ([3, 20.1], 0), ([-3, 0], 0)]
)
def test_draft_orders_query_with_filter_base_total_price_one_of(
    draft_order, one_of, count
):
    # given
    order = draft_order
    currency = order.currency
    order.total_net_amount = Decimal(20)
    order.save(update_fields=["total_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "currency": currency,
        "base_total_price": {"one_of": one_of},
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        OrderDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == count
    if count:
        assert result.first() == order


@pytest.mark.parametrize(
    ("one_of", "count"), [([1, 20, 70], 1), ([3, 20.1], 0), ([-3, 0], 0)]
)
def test_draft_orders_query_with_filter_base_subtotal_price_one_of(
    draft_order, one_of, count
):
    # given
    order = draft_order
    currency = order.currency
    order.subtotal_net_amount = Decimal(20)
    order.save(update_fields=["subtotal_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "currency": currency,
        "base_subtotal_price": {"one_of": one_of},
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        OrderDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == count
    if count:
        assert result.first() == order


def test_draft_orders_query_with_filter_base_total_price_missing_currency(draft_order):
    # given
    order = draft_order
    order.total_net_amount = Decimal(20)
    order.save(update_fields=["total_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "base_total_price": {
            "range": {
                "gte": 20,
            }
        },
    }

    # when
    with pytest.raises(ValidationError) as validation_error:
        where_filter_qs(
            qs,
            {},
            OrderDiscountedObjectWhere,
            predicate_data,
            None,
        )

    # then
    assert validation_error.value.code == "required"


def test_draft_orders_query_with_filter_base_subtotal_price_missing_currency(
    draft_order,
):
    # given
    order = draft_order
    order.subtotal_net_amount = Decimal(20)
    order.save(update_fields=["subtotal_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "base_subtotal_price": {
            "range": {
                "gte": 20,
            }
        },
    }

    # when
    with pytest.raises(ValidationError) as validation_error:
        where_filter_qs(
            qs,
            {},
            OrderDiscountedObjectWhere,
            predicate_data,
            None,
        )

    # then
    assert validation_error.value.code == "required"


def test_draft_orders_query_with_filter_price_with_and_or(draft_order):
    # given
    order = draft_order
    currency = order.currency
    order.total_net_amount = Decimal(20)
    order.save(update_fields=["total_net_amount"])

    qs = Order.objects.all()
    predicate_data = {
        "AND": [
            {
                "OR": [
                    {
                        "currency": currency,
                        "base_total_price": {
                            "range": {
                                "gte": 20,
                            }
                        },
                    },
                    {
                        "currency": currency,
                        "base_total_price": {
                            "range": {
                                "gte": 10,
                            }
                        },
                    },
                ]
            }
        ],
    }

    # when
    result = where_filter_qs(
        qs,
        {},
        OrderDiscountedObjectWhere,
        predicate_data,
        None,
    )

    # then
    assert result.count() == 1
