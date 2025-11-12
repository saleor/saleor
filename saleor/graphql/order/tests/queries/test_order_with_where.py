import datetime
from uuid import uuid4

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import Address
from .....core.postgres import FlatConcatSearchVector
from .....giftcard.events import gift_cards_bought_event, gift_cards_used_in_order_event
from .....invoice.models import Invoice
from .....order import (
    FulfillmentStatus,
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderStatus,
)
from .....order.models import FulfillmentLine, Order, OrderEvent, OrderLine
from .....order.search import prepare_order_search_vector_value
from .....warehouse.models import Stock
from ....core.utils import to_global_id_or_none
from ....tests.utils import get_graphql_content, get_graphql_content_from_response


@pytest.fixture
def orders_with_fulfillments(
    order_list, warehouses, order_lines_generator, product_variant_list
):
    statuses = [
        FulfillmentStatus.FULFILLED,
        FulfillmentStatus.REFUNDED,
        FulfillmentStatus.RETURNED,
    ]
    metadata_values = [
        {"foo": "bar"},
        {"foo": "zaz"},
        {},
    ]
    variant_1 = product_variant_list[0]
    variant_2 = product_variant_list[1]
    variant_1_quantity = 10
    variant_2_quantity = 5
    stock_1, stock_2 = Stock.objects.bulk_create(
        [
            Stock(
                product_variant=variant_1,
                warehouse=warehouses[0],
                quantity=variant_1_quantity * len(order_list),
            ),
            Stock(
                product_variant=variant_2,
                warehouse=warehouses[1],
                quantity=variant_2_quantity * len(order_list),
            ),
        ]
    )
    for order, status, metadata in zip(
        order_list, statuses, metadata_values, strict=True
    ):
        fulfillment = order.fulfillments.create(
            tracking_number="123", status=status, metadata=metadata
        )
        line_1, line_2 = order_lines_generator(
            order,
            [variant_1, variant_2],
            [10, 20],
            [variant_1_quantity, variant_2_quantity],
            create_allocations=False,
        )

        fulfillment.lines.create(
            order_line=line_1, quantity=line_1.quantity, stock=stock_1
        )
        fulfillment.lines.create(
            order_line=line_2, quantity=line_2.quantity, stock=stock_2
        )
    return order_list


def test_order_query_with_filter_and_where(
    staff_api_client,
    permission_group_manage_orders,
    orders,
):
    # given
    query = """
        query ($where: OrderWhereInput!, $filter: OrderFilterInput!) {
            orders(first: 10, where: $where, filter: $filter) {
                totalCount
                edges {
                    node {
                        id
                    }
                }
            }
        }
    """
    variables = {
        "where": {
            "status": {
                "eq": OrderStatus.UNFULFILLED.upper(),
            },
        },
        "filter": {
            "search": "test",
        },
    }
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    error_message = "Only one filtering argument (filter or where) can be specified."

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content_from_response(response)
    assert content["errors"][0]["message"] == error_message
    assert not content["data"]["orders"]


ORDERS_WHERE_QUERY = """
    query($where: OrderWhereInput!, $search: String) {
      orders(first: 10, search: $search, where: $where) {
        edges {
          node {
            id
            number
            created
            updatedAt
          }
        }
      }
    }
"""


def test_order_filter_by_ids(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    channel_USD,
    channel_PLN,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ids = [graphene.Node.to_global_id("Order", order.pk) for order in order_list[:2]]
    variables = {"where": {"ids": ids}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(order_list[0].number),
        str(order_list[1].number),
    }


def test_order_filter_by_none_as_ids(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"ids": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_ids_empty_list(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"ids": []}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() + datetime.timedelta(days=3)).isoformat(),
                "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "gte": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
            },
            [0, 1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
            },
            [],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_orders_filter_by_created_at(
    where,
    indexes,
    order,
    order_generator,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    with freeze_time((timezone.now() + datetime.timedelta(days=5)).isoformat()):
        order_2 = order_generator()

    with freeze_time((timezone.now() + datetime.timedelta(days=10)).isoformat()):
        order_3 = order_generator()

    order_list = [order, order_2, order_3]

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"createdAt": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() + datetime.timedelta(days=3)).isoformat(),
                "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
            },
            [0, 1],
        ),
        (
            {
                "gte": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
            },
            [0],
        ),
        (
            {
                "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
            },
            [0, 1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
            },
            [],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_orders_filter_by_updated_at(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    order_list[0].updated_at = timezone.now() + datetime.timedelta(days=15)
    order_list[1].updated_at = timezone.now() + datetime.timedelta(days=3)
    order_list[2].updated_at = timezone.now() + datetime.timedelta(days=1)
    Order.objects.bulk_update(order_list, ["updated_at"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"updatedAt": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


def test_order_filter_by_users(
    staff_api_client, permission_group_manage_orders, order_list, user_list, channel_USD
):
    # given
    order_list[0].user = user_list[0]
    order_list[1].user = user_list[1]
    order_list[2].user = user_list[2]
    Order.objects.bulk_update(order_list, ["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    type_ids = [graphene.Node.to_global_id("User", type.pk) for type in user_list[:2]]
    variables = {
        "where": {"user": {"oneOf": type_ids}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(order_list[0].number),
        str(order_list[1].number),
    }


def test_order_filter_by_user(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD, user_list
):
    # given
    order_list[0].user = user_list[0]
    order_list[0].save(update_fields=["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    type_id = graphene.Node.to_global_id("User", user_list[0].pk)

    variables = {
        "where": {"user": {"eq": type_id}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order_list[0].number) == orders[0]["node"]["number"]


def test_order_filter_by_none_as_user(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD, user_list
):
    # given
    order_list[0].user = user_list[0]
    order_list[0].save(update_fields=["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"user": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_user_emails(
    staff_api_client, permission_group_manage_orders, order_list, user_list, channel_USD
):
    # given
    order_list[0].user_email = user_list[0].email
    order_list[1].user_email = user_list[1].email
    order_list[2].user_email = user_list[2].email
    Order.objects.bulk_update(order_list, ["user_email"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    emails = [user_list[1].email, user_list[2].email]
    variables = {
        "where": {"userEmail": {"oneOf": emails}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(order_list[1].number),
        str(order_list[2].number),
    }


def test_order_filter_by_user_email(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD, user_list
):
    # given
    order_list[1].user_email = user_list[0].email
    order_list[1].save(update_fields=["user_email"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"userEmail": {"eq": user_list[0].email}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order_list[1].number) == orders[0]["node"]["number"]


def test_order_filter_by_none_as_user_email(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD, user_list
):
    # given
    order_list[0].user_email = user_list[0].email
    order_list[0].save(update_fields=["user_email"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"userEmail": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_numbers(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    numbers = [order_list[1].number, order_list[2].number]
    variables = {
        "where": {"number": {"oneOf": numbers}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(order_list[1].number),
        str(order_list[2].number),
    }


def test_order_filter_by_numbers_range(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ordered_orders = Order.objects.order_by("number")
    variables = {
        "where": {
            "number": {
                "range": {
                    "lte": ordered_orders[1].number,
                }
            }
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(order_list[0].number),
        str(order_list[1].number),
    }


def test_order_filter_by_number(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    order,
    channel_USD,
    user_list,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": order.number}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order.number) == orders[0]["node"]["number"]


def test_order_filter_by_none_as_number(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_number_nothing_returned(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": "11111111"}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_channel_id(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    channel_USD,
    channel_PLN,
):
    # given
    order_list[0].channel = channel_USD
    order_list[1].channel = channel_PLN
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {
            "channelId": {"eq": graphene.Node.to_global_id("Channel", channel_USD.id)}
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[0].number), str(order_list[2].number)}


def test_order_filter_by_channel_ids(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    channel_USD,
    channel_PLN,
):
    # given
    order_list[0].channel = channel_USD
    order_list[1].channel = channel_PLN
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {
            "channelId": {
                "oneOf": [
                    graphene.Node.to_global_id("Channel", channel.id)
                    for channel in [channel_USD, channel_PLN]
                ]
            }
        }
    }

    # then
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 3
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(order_list[0].number),
        str(order_list[1].number),
        str(order_list[2].number),
    }


def test_order_filter_by_channel_id_none(
    staff_api_client,
    permission_group_manage_orders,
    order_list,
    channel_USD,
    channel_PLN,
):
    # given
    order_list[0].channel = channel_USD
    order_list[1].channel = channel_PLN
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"where": {"channelId": {"eq": None}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"eq": OrderAuthorizeStatus.FULL.upper()}, [0]),
        ({"eq": OrderAuthorizeStatus.PARTIAL.upper()}, [1]),
        ({"oneOf": [OrderAuthorizeStatus.NONE.upper()]}, [2]),
        (
            {
                "oneOf": [
                    OrderAuthorizeStatus.FULL.upper(),
                    OrderAuthorizeStatus.PARTIAL.upper(),
                ]
            },
            [0, 1],
        ),
        ({"oneOf": [OrderAuthorizeStatus.FULL.upper()]}, [0]),
        ({}, []),
        ({"oneOf": []}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_orders_filter_by_authorize_status(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    order_list[0].authorize_status = OrderAuthorizeStatus.FULL
    order_list[1].authorize_status = OrderAuthorizeStatus.PARTIAL
    order_list[2].authorize_status = OrderAuthorizeStatus.NONE
    Order.objects.bulk_update(order_list, ["authorize_status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"authorizeStatus": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"eq": OrderChargeStatus.FULL.upper()}, []),
        ({"eq": OrderChargeStatus.PARTIAL.upper()}, [1]),
        ({"oneOf": [OrderChargeStatus.NONE.upper()]}, [2]),
        (
            {
                "oneOf": [
                    OrderChargeStatus.FULL.upper(),
                    OrderChargeStatus.PARTIAL.upper(),
                ]
            },
            [1],
        ),
        ({"eq": OrderChargeStatus.OVERCHARGED.upper()}, [0]),
        ({}, []),
        ({"oneOf": []}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_orders_filter_by_charge_status(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    order_list[0].charge_status = OrderChargeStatus.OVERCHARGED
    order_list[1].charge_status = OrderChargeStatus.PARTIAL
    order_list[2].charge_status = OrderChargeStatus.NONE
    Order.objects.bulk_update(order_list, ["charge_status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"chargeStatus": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"eq": OrderStatus.UNFULFILLED.upper()}, [0]),
        ({"eq": OrderStatus.UNCONFIRMED.upper()}, [1]),
        ({"oneOf": [OrderStatus.FULFILLED.upper()]}, [2]),
        (
            {"oneOf": [OrderStatus.UNFULFILLED.upper(), OrderStatus.CANCELED.upper()]},
            [0],
        ),
        ({"eq": OrderStatus.EXPIRED.upper()}, []),
        ({}, []),
        ({"oneOf": []}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_orders_filter_by_status(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    order_list[0].status = OrderStatus.UNFULFILLED
    order_list[1].status = OrderStatus.UNCONFIRMED
    order_list[2].status = OrderStatus.FULFILLED
    Order.objects.bulk_update(order_list, ["status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"status": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


def test_order_filter_by_checkout_tokens(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    ch_token_1 = uuid4()
    ch_token_2 = uuid4()
    ch_token_3 = uuid4()

    order_list[0].checkout_token = ch_token_1
    order_list[1].checkout_token = ch_token_2
    order_list[2].checkout_token = ch_token_3
    Order.objects.bulk_update(order_list, ["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"checkoutToken": {"oneOf": [ch_token_1, ch_token_3]}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(order_list[0].number),
        str(order_list[2].number),
    }


def test_order_filter_by_checkout_token(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    token = uuid4()
    order_list[0].checkout_token = token
    order_list[0].save(update_fields=["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {"checkoutToken": {"eq": token}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order_list[0].number) == orders[0]["node"]["number"]


def test_order_filter_by_none_as_checkout_token(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    order_list[0].checkout_token = uuid4()
    order_list[0].save(update_fields=["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {"checkoutToken": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_by_checkout_ids(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    ch_token_1 = uuid4()
    ch_token_2 = uuid4()
    ch_token_3 = uuid4()

    order_list[0].checkout_token = ch_token_1
    order_list[1].checkout_token = ch_token_2
    order_list[2].checkout_token = ch_token_3
    Order.objects.bulk_update(order_list, ["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "checkoutId": {
                "oneOf": [
                    graphene.Node.to_global_id("Checkout", token)
                    for token in [ch_token_1, ch_token_3]
                ]
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(order_list[0].number),
        str(order_list[2].number),
    }


def test_order_filter_by_checkout_id(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    token = uuid4()
    order_list[0].checkout_token = token
    order_list[0].save(update_fields=["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {"checkoutId": {"eq": graphene.Node.to_global_id("Checkout", token)}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order_list[0].number) == orders[0]["node"]["number"]


def test_order_filter_by_none_as_checkout_id(
    staff_api_client, permission_group_manage_orders, order_list, channel_USD
):
    # given
    order_list[0].checkout_token = uuid4()
    order_list[0].save(update_fields=["checkout_token"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {"checkoutId": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_is_click_and_collect_true(
    staff_api_client,
    permission_group_manage_orders,
    order_list_with_cc_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    orders = order_list_with_cc_orders
    variables = {"where": {"isClickAndCollect": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    expected_orders = {
        order
        for order in orders
        if order.collection_point or order.collection_point_name
    }
    assert len(returned_orders) == len(expected_orders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in expected_orders
    }


def test_order_filter_is_click_and_collect_false(
    staff_api_client,
    permission_group_manage_orders,
    order_list_with_cc_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    orders = order_list_with_cc_orders
    variables = {"where": {"isClickAndCollect": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    expected_orders = {
        order
        for order in orders
        if not order.collection_point
        and not order.collection_point_name
        and order.status != OrderStatus.DRAFT
    }
    assert len(returned_orders) == len(expected_orders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in expected_orders
    }


def test_order_filter_is_click_and_collect_none(
    staff_api_client,
    permission_group_manage_orders,
    order_list_with_cc_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isClickAndCollect": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    assert len(returned_orders) == 0


def test_order_filter_gift_card_used_true(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[0]
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"where": {"isGiftCardUsed": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["id"] == graphene.Node.to_global_id(
        "Order", gift_card_order.id
    )


def test_order_filter_gift_card_used_false(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[0]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"where": {"isGiftCardUsed": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


def test_order_filter_gift_card_used_none(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[0]
    gift_cards_used_in_order_event(
        [(gift_card, 20.0)], gift_card_order, staff_api_client.user, None
    )
    variables = {"where": {"isGiftCardUsed": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_order_filter_gift_card_bough_true(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[-1]
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"where": {"isGiftCardBought": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["id"] == graphene.Node.to_global_id(
        "Order", gift_card_order.id
    )


def test_order_filter_gift_card_bought_false(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[-1]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"where": {"isGiftCardBought": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


def test_order_filter_gift_card_bought_none(
    staff_api_client,
    permission_group_manage_orders,
    gift_card,
    orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    gift_card_order = orders[-1]
    gift_card_order_id = graphene.Node.to_global_id("Order", gift_card_order.id)
    gift_cards_bought_event([gift_card], gift_card_order, staff_api_client.user, None)
    variables = {"where": {"isGiftCardBought": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders_data = content["data"]["orders"]["edges"]
    assert gift_card_order_id not in {
        order_data["node"]["id"] for order_data in orders_data
    }


def test_order_filter_with_search_and_charge_status(
    staff_api_client,
    permission_group_manage_orders,
    orders,
    customer_user,
):
    # given
    customer_user.first_name = "Search test Saleor"
    customer_user.save()
    for order in orders[:-1]:
        order.user = customer_user
        order.search_vector = FlatConcatSearchVector(
            *prepare_order_search_vector_value(order)
        )

    order_full_charge_1 = orders[0]
    order_full_charge_1.charge_status = OrderChargeStatus.FULL
    order_full_charge_2 = orders[2]
    order_full_charge_2.charge_status = OrderChargeStatus.FULL
    order_partial_charge = orders[1]
    order_partial_charge.charge_status = OrderChargeStatus.PARTIAL
    order_full_charge_not_included_in_search = orders[-1]
    order_full_charge_not_included_in_search.charge_status = OrderChargeStatus.FULL

    Order.objects.bulk_update(orders, ["search_vector", "user", "charge_status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "search": "test",
        "where": {
            "chargeStatus": {"eq": OrderChargeStatus.FULL.upper()},
        },
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(order_full_charge_1.number),
        str(order_full_charge_2.number),
    }


def test_orders_filter_by_voucher_code_eq(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    order_list[0].voucher_code = codes[0].code
    order_list[1].voucher_code = codes[1].code
    order_list[1].voucher = voucher_with_many_codes
    order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": {"eq": codes[0].code}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["number"] == str(order_list[0].number)


def test_orders_filter_by_voucher_code_one_of(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    order_list[0].voucher_code = codes[0].code
    order_list[1].voucher_code = codes[1].code
    order_list[1].voucher = voucher_with_many_codes
    order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": {"oneOf": [codes[1].code, codes[2].code]}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(order_list[1].number),
        str(order_list[2].number),
    }


@pytest.mark.parametrize(
    "where",
    [
        {},
        {"oneOf": []},
        {"eq": None},
        None,
    ],
)
def test_orders_filter_by_voucher_code_empty_value(
    where,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    order_list[0].voucher_code = codes[0].code
    order_list[1].voucher_code = codes[1].code
    order_list[1].voucher = voucher_with_many_codes
    order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_orders_filter_by_has_invoices_true(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        Invoice.objects.create(order=order)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasInvoices": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(order_list[1:])
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {str(o.number) for o in order_list[1:]}


def test_orders_filter_by_has_invoices_false(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        Invoice.objects.create(order=order)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasInvoices": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {str(order_list[0].number)}


def test_orders_filter_by_has_invoices_none(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        Invoice.objects.create(order=order)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasInvoices": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            [
                {
                    "createdAt": {
                        "lte": (
                            timezone.now() - datetime.timedelta(days=3)
                        ).isoformat(),
                        "gte": (
                            timezone.now() - datetime.timedelta(days=25)
                        ).isoformat(),
                    }
                },
                {
                    "createdAt": {
                        "gte": (
                            timezone.now() - datetime.timedelta(days=15)
                        ).isoformat(),
                    }
                },
            ],
            [1, 2],
        ),
        (
            [
                {
                    "createdAt": {
                        "lte": (
                            timezone.now() - datetime.timedelta(days=4)
                        ).isoformat(),
                    }
                },
                {
                    "createdAt": {
                        "gte": (
                            timezone.now() - datetime.timedelta(days=9)
                        ).isoformat(),
                    }
                },
            ],
            [1, 2],
        ),
        (
            [
                {
                    "createdAt": {
                        "lte": (
                            timezone.now() - datetime.timedelta(days=9)
                        ).isoformat(),
                    }
                }
            ],
            [2],
        ),
        (
            [
                {
                    "createdAt": {
                        "gte": (
                            timezone.now() - datetime.timedelta(days=2)
                        ).isoformat(),
                    }
                }
            ],
            [0],
        ),
        (None, []),
        ([{"createdAt": {"gte": None}}], []),
        ([{"createdAt": {"lte": None}}], []),
        ([{"createdAt": {"lte": None, "gte": None}}], []),
        ([{}], []),
    ],
)
def test_orders_filter_by_invoices(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    Invoice.objects.create(order=order_list[0])

    with freeze_time((timezone.now() - datetime.timedelta(days=5)).isoformat()):
        Invoice.objects.create(order=order_list[1])
        Invoice.objects.create(order=order_list[2])

    with freeze_time((timezone.now() - datetime.timedelta(days=10)).isoformat()):
        Invoice.objects.create(order=order_list[2])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"invoices": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


def test_orders_filter_by_has_fulfillments_true(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        order.fulfillments.create(tracking_number="123")

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasFulfillments": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(order_list[1:])
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {str(o.number) for o in order_list[1:]}


def test_orders_filter_by_has_fulfillments_false(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        order.fulfillments.create(tracking_number="123")

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasFulfillments": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {str(order_list[0].number)}


def test_orders_filter_by_has_fulfillments_none(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    for order in order_list[1:]:
        order.fulfillments.create(tracking_number="123")

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"hasFulfillments": None}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ([{"status": {"eq": FulfillmentStatus.FULFILLED.upper()}}], [0]),
        ([{"status": {"eq": FulfillmentStatus.REFUNDED.upper()}}], [1]),
        ([{"status": {"eq": FulfillmentStatus.RETURNED.upper()}}], [2]),
        (
            [
                {
                    "status": {
                        "oneOf": [
                            FulfillmentStatus.FULFILLED.upper(),
                            FulfillmentStatus.REFUNDED.upper(),
                        ]
                    }
                }
            ],
            [0, 1],
        ),
        (
            [
                {
                    "status": {
                        "oneOf": [
                            FulfillmentStatus.REPLACED.upper(),
                            FulfillmentStatus.CANCELED.upper(),
                        ]
                    }
                }
            ],
            [],
        ),
        ([{"status": {"eq": FulfillmentStatus.WAITING_FOR_APPROVAL.upper()}}], []),
        ([{}], []),
        ([{"status": {"oneOf": []}}], []),
        ([{"status": {"eq": None}}], []),
        (None, []),
    ],
)
def test_orders_filter_by_fulfillment_status(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    statuses = [
        FulfillmentStatus.FULFILLED,
        FulfillmentStatus.REFUNDED,
        FulfillmentStatus.RETURNED,
    ]
    for order, status in zip(order_list, statuses, strict=True):
        order.fulfillments.create(tracking_number="123", status=status)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"fulfillments": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("where", "expected_indexes"),
    [
        ([{"metadata": {"key": "foo"}}], [0, 1]),
        ([{"metadata": {"key": "foo", "value": {"eq": "bar"}}}], [0]),
        ([{"metadata": {"key": "foo", "value": {"eq": "baz"}}}], []),
        ([{"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}}], [0, 1]),
        ([{"metadata": {"key": "notfound"}}], []),
        ([{"metadata": {"key": "foo", "value": {"eq": None}}}], []),
        ([{"metadata": {"key": "foo", "value": {"oneOf": []}}}], []),
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}},
            ],
            [0, 1],
        ),
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "notfound"}},
            ],
            [],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "bar"}}},
                {"metadata": {"key": "baz", "value": {"eq": "zaz"}}},
            ],
            [],
        ),
        (
            [
                {"metadata": {"key": "baz"}},
                {"metadata": {"key": "foo", "value": {"eq": "zaz"}}},
            ],
            [1],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}},
                {"metadata": {"key": "baz"}},
            ],
            [1],
        ),
        (None, []),
    ],
)
def test_orders_filter_by_fulfillment_metadata(
    where,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    metadata_values = [
        {"foo": "bar"},
        {"foo": "zaz", "baz": "zaz"},
        {},
    ]
    for order, metadata_value in zip(order_list, metadata_values, strict=True):
        order.fulfillments.create(tracking_number="123", metadata=metadata_value)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"fulfillments": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("fulfillment_filter", "expected_indexes"),
    [
        (
            [
                {"status": {"eq": FulfillmentStatus.FULFILLED.upper()}},
                {"metadata": {"key": "foo"}},
            ],
            [0],
        ),
        (
            [
                {"status": {"eq": FulfillmentStatus.REFUNDED.upper()}},
                {"metadata": {"key": "foo", "value": {"eq": "zaz"}}},
            ],
            [1],
        ),
        (
            [
                {"status": {"eq": FulfillmentStatus.RETURNED.upper()}},
                {"metadata": {"key": "baz"}},
            ],
            [],
        ),
        (
            [
                {
                    "status": {
                        "oneOf": [
                            FulfillmentStatus.FULFILLED.upper(),
                            FulfillmentStatus.REFUNDED.upper(),
                        ]
                    }
                },
                {"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}},
            ],
            [0, 1],
        ),
        (
            [
                {"status": {"eq": FulfillmentStatus.FULFILLED.upper()}},
                {"metadata": {"key": "notfound"}},
            ],
            [],
        ),
        (
            [
                {"status": {"eq": FulfillmentStatus.RETURNED.upper()}},
                {"metadata": {"key": "foo", "value": {"eq": "baz"}}},
            ],
            [],
        ),
        (
            [
                {"status": {}},
                {"metadata": {"key": "foo"}},
            ],
            [0, 1],
        ),
        (
            [],
            [],
        ),
    ],
)
def test_orders_filter_fulfillment_status_and_metadata_both_match(
    fulfillment_filter,
    expected_indexes,
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"fulfillments": fulfillment_filter}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == len(expected_indexes)
    assert {node["node"]["number"] for node in orders} == {
        str(orders_with_fulfillments[i].number) for i in expected_indexes
    }


def test_orders_filter_fulfillment_status_matches_metadata_not(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": {"eq": FulfillmentStatus.FULFILLED.upper()},
                    "metadata": {"key": "foo", "value": {"eq": "notfound"}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


def test_orders_filter_fulfillment_metadata_matches_status_not(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": {"eq": FulfillmentStatus.REFUNDED.upper()},
                    "metadata": {"key": "foo", "value": {"eq": "bar"}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


def test_orders_filter_fulfillment_status_and_metadata_both_not_match(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": {"eq": FulfillmentStatus.RETURNED.upper()},
                    "metadata": {"key": "foo", "value": {"eq": "baz"}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


def test_orders_filter_fulfillment_status_matches_metadata_none(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": {"eq": FulfillmentStatus.FULFILLED.upper()},
                    "metadata": None,
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    assert {node["node"]["number"] for node in orders} == {
        str(orders_with_fulfillments[0].number)
    }


def test_orders_filter_fulfillment_metadata_matches_status_none(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": None,
                    "metadata": {"key": "foo", "value": {"eq": "bar"}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    assert {node["node"]["number"] for node in orders} == {
        str(orders_with_fulfillments[0].number)
    }


def test_orders_filter_fulfillment_status_and_metadata_both_none(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": None,
                    "metadata": None,
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


def test_orders_filter_fulfillment_status_oneof_metadata_oneof(
    orders_with_fulfillments, staff_api_client, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "fulfillments": [
                {
                    "status": {
                        "oneOf": [
                            FulfillmentStatus.FULFILLED.upper(),
                            FulfillmentStatus.REFUNDED.upper(),
                        ]
                    },
                    "metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 2
    assert {node["node"]["number"] for node in orders} == {
        str(orders_with_fulfillments[0].number),
        str(orders_with_fulfillments[1].number),
    }


def test_orders_filter_fulfillment_warehouse_id_eq(
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order
    fulfillment = expected_order.fulfillments.first()
    warehouse = fulfillment.lines.first().stock.warehouse

    variables = {
        "where": {
            "fulfillments": [
                {"warehouse": {"id": {"eq": to_global_id_or_none(warehouse)}}}
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    order_number_from_api = orders[0]["node"]["number"]
    assert order_number_from_api == str(expected_order.number)


def test_orders_filter_fulfillment_warehouse_id_one_of(
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order
    fulfillment = expected_order.fulfillments.first()
    warehouse = fulfillment.lines.first().stock.warehouse

    variables = {
        "where": {
            "fulfillments": [
                {"warehouse": {"id": {"oneOf": [to_global_id_or_none(warehouse)]}}}
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    order_number_from_api = orders[0]["node"]["number"]
    assert order_number_from_api == str(expected_order.number)


@pytest.mark.parametrize(
    "where_warehouse_slug",
    [
        {"slug": {"eq": "warehouse-to-get"}},
        {"slug": {"oneOf": ["warehouse-to-get"]}},
    ],
)
def test_orders_filter_fulfillment_warehouse_slug(
    where_warehouse_slug,
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order
    fulfillment = expected_order.fulfillments.first()

    assert FulfillmentLine.objects.count() > 1

    warehouse = fulfillment.lines.first().stock.warehouse

    expected_warehouse_slug = "warehouse-to-get"
    warehouse.slug = expected_warehouse_slug
    warehouse.save()

    variables = {"where": {"fulfillments": [{"warehouse": where_warehouse_slug}]}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    order_number_from_api = orders[0]["node"]["number"]
    assert order_number_from_api == str(expected_order.number)


@pytest.mark.parametrize(
    "where_warehouse_external_reference",
    [
        {"externalReference": {"eq": "warehouse-to-get"}},
        {"externalReference": {"oneOf": ["warehouse-to-get"]}},
    ],
)
def test_orders_filter_fulfillment_warehouse_external_reference(
    where_warehouse_external_reference,
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order
    fulfillment = expected_order.fulfillments.first()

    assert FulfillmentLine.objects.count() > 1

    warehouse = fulfillment.lines.first().stock.warehouse

    expected_warehouse_external_reference = "warehouse-to-get"
    warehouse.external_reference = expected_warehouse_external_reference
    warehouse.save()

    variables = {
        "where": {"fulfillments": [{"warehouse": where_warehouse_external_reference}]}
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    order_number_from_api = orders[0]["node"]["number"]
    assert order_number_from_api == str(expected_order.number)


@pytest.mark.parametrize(
    "where_warehouse_non_existing_input",
    [
        {"externalReference": {"eq": "non-existing-warehouse"}},
        {"externalReference": {"oneOf": ["non-existing-warehouse"]}},
        {"slug": {"eq": "non-existing-warehouse"}},
        {"slug": {"oneOf": ["non-existing-warehouse"]}},
        {
            "id": {
                "eq": "V2FyZWhvdXNlOjJjMGNiODAwLTU0N2ItNDM1ZS04Y2UwLTkyYTFiOTE1ZmFkMQ=="
            }
        },
        {
            "id": {
                "oneOf": [
                    "V2FyZWhvdXNlOjJjMGNiODAwLTU0N2ItNDM1ZS04Y2UwLTkyYTFiOTE1ZmFkMQ=="
                ]
            }
        },
        {
            "slug": {"oneOf": ["non-existing-warehouse"]},
            "externalReference": {"eq": "existing-warehouse-ref"},
        },
    ],
)
def test_orders_filter_fulfillment_warehouse_non_existing(
    where_warehouse_non_existing_input,
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    fulfillment = fulfilled_order.fulfillments.first()

    assert FulfillmentLine.objects.count() > 1

    existing_warehouse = fulfillment.lines.first().stock.warehouse
    existing_warehouse.slug = "existing-warehouse-slug"
    existing_warehouse.external_reference = "existing-warehouse-ref"
    existing_warehouse.save()

    variables = {
        "where": {"fulfillments": [{"warehouse": where_warehouse_non_existing_input}]}
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


@pytest.mark.parametrize(
    "where_additional_filters",
    [
        {"status": {"eq": FulfillmentStatus.FULFILLED.upper()}},
        {"metadata": {"key": "notfound"}},
    ],
)
def test_orders_filter_fulfillment_warehouse_with_multiple_filters_with_no_match(
    where_additional_filters,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order
    fulfillment = expected_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.WAITING_FOR_APPROVAL
    fulfillment.metadata = {"key": "value"}
    fulfillment.save()

    warehouse = fulfillment.lines.first().stock.warehouse

    variables = {
        "where": {
            "fulfillments": [
                {
                    "warehouse": {"id": {"eq": to_global_id_or_none(warehouse)}},
                    **where_additional_filters,
                },
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 0


@pytest.mark.parametrize(
    "where_additional_filters",
    [
        {"status": {"eq": FulfillmentStatus.FULFILLED.upper()}},
        {"metadata": {"key": "meta-key"}},
    ],
)
def test_orders_filter_fulfillment_warehouse_multiple_filters(
    where_additional_filters,
    orders_with_fulfillments,
    staff_api_client,
    permission_group_manage_orders,
    fulfilled_order,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    expected_order = fulfilled_order

    fulfillment = expected_order.fulfillments.first()
    fulfillment.status = FulfillmentStatus.FULFILLED
    fulfillment.metadata = {"meta-key": "meta-value"}
    fulfillment.save()

    assert FulfillmentLine.objects.count() > 1

    warehouse = fulfillment.lines.first().stock.warehouse

    expected_warehouse_external_reference = "warehouse-to-get"
    warehouse.external_reference = expected_warehouse_external_reference
    warehouse.save()

    variables = {
        "where": {
            "fulfillments": [
                {
                    "warehouse": {"id": {"eq": to_global_id_or_none(warehouse)}},
                    **where_additional_filters,
                },
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]

    # then
    assert len(orders) == 1
    order_number_from_api = orders[0]["node"]["number"]
    assert order_number_from_api == str(expected_order.number)


@pytest.mark.parametrize(
    ("filter_input", "expected_indexes"),
    [
        ([{"metadata": {"key": "foo"}}], [0, 1]),
        ([{"metadata": {"key": "foo", "value": {"eq": "bar"}}}], [0]),
        ([{"metadata": {"key": "foo", "value": {"eq": "baz"}}}], []),
        ([{"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}}], [0, 1]),
        ([{"metadata": {"key": "notfound"}}], []),
        ([{"metadata": {"key": "foo", "value": {"eq": None}}}], []),
        ([{"metadata": {"key": "foo", "value": {"oneOf": []}}}], []),
        (None, []),
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "foo", "value": {"eq": "bar"}}},
            ],
            [0],
        ),
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "baz", "value": {"eq": "zaz"}}},
            ],
            [0, 1],
        ),
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "foo", "value": {"eq": "baz"}}},
            ],
            [],
        ),
    ],
)
def test_orders_filter_by_lines_metadata(
    filter_input,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    metadata_values = [
        {
            "foo": "bar",
            "baz": "zaz",
        },
        {
            "foo": "zaz",
            "baz": "zaz",
        },
        {},
    ]
    for order, metadata_value in zip(order_list, metadata_values, strict=True):
        lines.append(
            OrderLine(
                order=order,
                product_name="Test Product",
                is_shipping_required=True,
                is_gift_card=False,
                quantity=2,
                currency="USD",
                unit_price_net_amount="10.00",
                unit_price_gross_amount="12.30",
                total_price_net_amount="20.00",
                total_price_gross_amount="24.60",
                metadata=metadata_value,
            )
        )
    OrderLine.objects.bulk_create(lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"lines": filter_input}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"range": {"gte": 2, "lte": 4}}, [1, 2]),
        ({"range": {"gte": 3}}, [2]),
        ({"range": {"lte": 2}}, [0, 1]),
        ({"eq": 2}, [1]),
        ({"oneOf": [1, 3]}, [0, 2]),
        ({"eq": 99}, []),
        ({}, []),
        ({"range": {"gte": None}}, []),
        ({"range": {"lte": None}}, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
        (None, []),
    ],
)
def test_orders_filter_by_lines_count(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_list[0].lines_count = 1
    order_list[1].lines_count = 2
    order_list[2].lines_count = 3
    Order.objects.bulk_update(order_list, ["lines_count"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"linesCount": where}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("currency", "where", "indexes"),
    [
        ("USD", {"range": {"gte": "100.00", "lte": "200.00"}}, [0, 1]),
        ("USD", {"range": {"gte": "150.00"}}, [1]),
        ("PLN", {"range": {"gte": "150.00"}}, [2]),
        (None, {"range": {"gte": "150.00"}}, [1, 2]),
        ("USD", {"range": {"lte": "120.00"}}, [0]),
        ("USD", {"eq": "150.00"}, [1]),
        ("PLN", {"eq": "150.00"}, []),
        ("USD", {"oneOf": ["100.00", "110.00"]}, [0]),
        ("USD", {}, []),
        (None, {"range": {"gte": None}}, []),
        ("USD", {"range": {"lte": None}}, []),
        ("USD", {"eq": None}, []),
        (None, {"eq": None}, []),
    ],
)
def test_orders_filter_by_total_gross(
    currency,
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_list[0].total_gross_amount = "110.00"
    order_list[0].currency = "USD"
    order_list[1].total_gross_amount = "150.00"
    order_list[1].currency = "USD"
    order_list[2].total_gross_amount = "200.00"
    order_list[2].currency = "PLN"
    Order.objects.bulk_update(order_list, ["total_gross_amount", "currency"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "totalGross": {
                "currency": currency,
                "amount": where,
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("currency", "where", "indexes"),
    [
        ("USD", {"range": {"gte": "100.00", "lte": "200.00"}}, [0, 1]),
        ("USD", {"range": {"gte": "150.00"}}, [1]),
        ("PLN", {"range": {"gte": "150.00"}}, [2]),
        (None, {"range": {"gte": "150.00"}}, [1, 2]),
        ("USD", {"range": {"lte": "120.00"}}, [0]),
        ("USD", {"eq": "150.00"}, [1]),
        ("PLN", {"eq": "150.00"}, []),
        ("USD", {"oneOf": ["100.00", "110.00"]}, [0]),
        ("USD", {}, []),
        (None, {"range": {"gte": None}}, []),
        ("USD", {"range": {"lte": None}}, []),
        ("USD", {"eq": None}, []),
        (None, {"eq": None}, []),
    ],
)
def test_orders_filter_by_total_net(
    currency,
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_list[0].total_net_amount = "110.00"
    order_list[0].currency = "USD"
    order_list[1].total_net_amount = "150.00"
    order_list[1].currency = "USD"
    order_list[2].total_net_amount = "200.00"
    order_list[2].currency = "PLN"
    Order.objects.bulk_update(order_list, ["total_net_amount", "currency"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {
        "where": {
            "totalNet": {
                "currency": currency,
                "amount": where,
            }
        }
    }

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("metadata", "expected_indexes"),
    [
        ({"key": "foo"}, [0, 1]),
        ({"key": "foo", "value": {"eq": "bar"}}, [0]),
        ({"key": "foo", "value": {"eq": "baz"}}, []),
        ({"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}, [0, 1]),
        ({"key": "notfound"}, []),
        ({"key": "foo", "value": {"eq": None}}, []),
        ({"key": "foo", "value": {"oneOf": []}}, []),
        (None, []),
    ],
)
def test_orders_filter_by_metadata(
    metadata,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    order_list[0].metadata = {"foo": "bar"}
    order_list[1].metadata = {"foo": "zaz"}
    order_list[2].metadata = {}
    Order.objects.bulk_update(order_list, ["metadata"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


def test_orders_filter_by_product_type_id(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(order_list, product_type_ids, strict=True):
        lines.append(
            OrderLine(
                order=order,
                product_name="Test Product",
                is_shipping_required=True,
                is_gift_card=False,
                quantity=2,
                currency="USD",
                unit_price_net_amount="10.00",
                unit_price_gross_amount="12.30",
                total_price_net_amount="20.00",
                total_price_gross_amount="24.60",
                product_type_id=product_type_id,
            )
        )
    OrderLine.objects.bulk_create(lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    product_type_id = graphene.Node.to_global_id("ProductType", 4)
    variables = {"where": {"productTypeId": {"eq": product_type_id}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 1
    assert str(order_list[1].number) == orders[0]["node"]["number"]


def test_orders_filter_by_product_type_ids(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(order_list, product_type_ids, strict=True):
        lines.append(
            OrderLine(
                order=order,
                product_name="Test Product",
                is_shipping_required=True,
                is_gift_card=False,
                quantity=2,
                currency="USD",
                unit_price_net_amount="10.00",
                unit_price_gross_amount="12.30",
                total_price_net_amount="20.00",
                total_price_gross_amount="24.60",
                product_type_id=product_type_id,
            )
        )
    OrderLine.objects.bulk_create(lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    product_type_ids = [
        graphene.Node.to_global_id("ProductType", id) for id in product_type_ids[:2]
    ]
    variables = {"where": {"productTypeId": {"oneOf": product_type_ids}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(order_list[:2])
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order.number) for order in order_list[:2]}


def test_orders_filter_by_product_type_ids_nothing_match(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(order_list, product_type_ids, strict=True):
        lines.append(
            OrderLine(
                order=order,
                product_name="Test Product",
                is_shipping_required=True,
                is_gift_card=False,
                quantity=2,
                currency="USD",
                unit_price_net_amount="10.00",
                unit_price_gross_amount="12.30",
                total_price_net_amount="20.00",
                total_price_gross_amount="24.60",
                product_type_id=product_type_id,
            )
        )
    OrderLine.objects.bulk_create(lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    product_type_ids = [graphene.Node.to_global_id("ProductType", id) for id in [6, 7]]
    variables = {"where": {"productTypeId": {"oneOf": product_type_ids}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


def test_orders_filter_by_product_type_none(
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(order_list, product_type_ids, strict=True):
        lines.append(
            OrderLine(
                order=order,
                product_name="Test Product",
                is_shipping_required=True,
                is_gift_card=False,
                quantity=2,
                currency="USD",
                unit_price_net_amount="10.00",
                unit_price_gross_amount="12.30",
                total_price_net_amount="20.00",
                total_price_gross_amount="24.60",
                product_type_id=product_type_id,
            )
        )
    OrderLine.objects.bulk_create(lines)

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"productTypeId": {"eq": None}}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("event_input", "expected_indexes"),
    [
        (
            [
                {
                    "date": {"gte": "2025-01-01T00:00:00Z"},
                    "type": {"eq": OrderEvents.PLACED.upper()},
                }
            ],
            [0, 1, 2],
        ),
        (
            [
                {
                    "date": {"gte": "2025-01-01T00:00:00Z"},
                    "type": {"eq": OrderEvents.ORDER_FULLY_PAID.upper()},
                }
            ],
            [0, 1],
        ),
        (
            [
                {
                    "date": {"gte": "2026-01-01T00:00:00Z"},
                }
            ],
            [],
        ),
        (
            [
                {
                    "date": {"gte": "2020-01-01T00:00:00Z"},
                }
            ],
            [0, 1, 2],
        ),
        (
            [
                {
                    "type": {
                        "oneOf": [
                            OrderEvents.PLACED.upper(),
                            OrderEvents.ORDER_FULLY_PAID.upper(),
                        ]
                    },
                }
            ],
            [0, 1, 2],
        ),
        (
            [
                {
                    "type": {"eq": OrderEvents.PLACED.upper()},
                },
                {
                    "type": {"eq": OrderEvents.ORDER_FULLY_PAID.upper()},
                },
            ],
            [0, 1],
        ),
        (
            [
                {
                    "date": {"gte": "2025-01-01T00:00:00Z"},
                    "type": {"oneOf": [OrderEvents.PLACED.upper()]},
                },
                {
                    "date": {"gte": "2025-02-01T00:00:00Z"},
                    "type": {"oneOf": [OrderEvents.ORDER_FULLY_PAID.upper()]},
                },
            ],
            [0, 1],
        ),
        (
            [
                {
                    "date": {"gte": "2025-01-01T00:00:00Z"},
                    "type": {"eq": OrderEvents.PLACED.upper()},
                },
                {
                    "date": {"gte": "2025-02-02T00:00:00Z"},
                },
            ],
            [0, 1],
        ),
    ],
)
def test_orders_filter_by_order_events(
    event_input,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    with freeze_time("2025-01-01T00:00:00Z"):
        OrderEvent.objects.bulk_create(
            [OrderEvent(order=order, type=OrderEvents.PLACED) for order in order_list]
        )

    with freeze_time("2025-02-02T00:00:00Z"):
        OrderEvent.objects.bulk_create(
            [
                OrderEvent(order=order, type=OrderEvents.ORDER_FULLY_PAID)
                for order in order_list[:2]
            ]
        )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"events": event_input}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "type": {"eq": "CARD"},
                        }
                    }
                ]
            },
            [0, 2],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "type": {"eq": "OTHER"},
                        }
                    }
                ]
            },
            [1],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "card": {
                                "brand": {"eq": "Brand"},
                            }
                        }
                    }
                ]
            },
            [0],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "card": {
                                "brand": {"eq": "Brand4"},
                            }
                        }
                    }
                ]
            },
            [2],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "card": {
                                "brand": {"eq": "Brand2"},
                            }
                        }
                    }
                ]
            },
            [0],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "type": {"oneOf": ["CARD", "OTHER"]},
                        }
                    }
                ]
            },
            [0, 1, 2],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "card": {
                                "brand": {"oneOf": ["Brand2", "Brand4"]},
                            }
                        }
                    }
                ]
            },
            [0, 2],
        ),
        (
            {
                "transactions": [
                    {
                        "paymentMethodDetails": {
                            "type": {"eq": "CARD"},
                        }
                    },
                    {
                        "paymentMethodDetails": {
                            "card": {"brand": {"eq": "Brand"}},
                        }
                    },
                ]
            },
            [0],
        ),
    ],
)
def test_orders_filter_by_transaction_payment_details(
    where,
    indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    transaction_item_generator,
):
    # given
    # first_transaction
    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Credit card",
        cc_brand="Brand",
        cc_first_digits="1234",
        cc_last_digits="5678",
        cc_exp_month=12,
        cc_exp_year=2025,
    )

    # second_transaction
    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Second Credit card",
        cc_brand="Brand2",
        cc_first_digits="1234",
        cc_last_digits="5678",
        cc_exp_month=12,
        cc_exp_year=2025,
    )

    # third_transaction
    transaction_item_generator(
        order_id=order_list[1].pk,
        charged_value=order_list[1].total.gross.amount,
        payment_method_type="other",
        payment_method_name="Third payment method",
        cc_brand=None,
        cc_first_digits=None,
        cc_last_digits=None,
        cc_exp_month=None,
        cc_exp_year=None,
    )

    # fourth_transaction
    transaction_item_generator(
        order_id=order_list[2].pk,
        charged_value=order_list[2].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Fourth Credit card",
        cc_brand="Brand4",
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": where}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[index].number) for index in indexes}


@pytest.mark.parametrize(
    ("metadata_list", "expected_indexes"),
    [
        (
            [
                {"metadata": {"key": "foo"}},
                {"metadata": {"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}},
            ],
            [0, 1],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "bar"}}},
                {"metadata": {"key": "foo", "value": {"eq": "zaz"}}},
            ],
            [],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "bar"}}},
                {"metadata": {"key": "notfound"}},
            ],
            [],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "zaz"}}},
                {"metadata": {"key": "foo"}},
            ],
            [1],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "baz"}}},
                {"metadata": {"key": "notfound"}},
            ],
            [],
        ),
    ],
)
def test_orders_filter_by_transaction_metadata(
    metadata_list,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    transaction_item_generator,
):
    # given
    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        metadata={"foo": "bar"},
    )

    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        metadata={},
    )

    transaction_item_generator(
        order_id=order_list[1].pk,
        charged_value=order_list[1].total.gross.amount,
        metadata={"foo": "zaz"},
    )

    transaction_item_generator(
        order_id=order_list[2].pk,
        charged_value=order_list[2].total.gross.amount,
        metadata={},
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"transactions": metadata_list}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("transaction_filters", "expected_indexes"),
    [
        (
            [
                {"metadata": {"key": "foo"}},
                {"paymentMethodDetails": {"type": {"eq": "CARD"}}},
            ],
            [0, 2],
        ),
        (
            [
                {"metadata": {"key": "foo"}},
                {"paymentMethodDetails": {"type": {"eq": "OTHER"}}},
            ],
            [1],
        ),
        (
            [
                {"metadata": {"key": "notfound"}},
                {"paymentMethodDetails": {"type": {"eq": "OTHER"}}},
            ],
            [],
        ),
        (
            [
                {"metadata": {"key": "foo", "value": {"eq": "baz"}}},
                {"paymentMethodDetails": {"type": {"eq": "CARD"}}},
            ],
            [0],
        ),
    ],
)
def test_orders_filter_by_transactions_with_mixed_conditions(
    transaction_filters,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
    transaction_item_generator,
):
    # given
    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Credit card",
        cc_brand="Brand",
        cc_first_digits="1234",
        cc_last_digits="5678",
        cc_exp_month=12,
        cc_exp_year=2025,
        metadata={},
    )

    # second_transaction
    transaction_item_generator(
        order_id=order_list[0].pk,
        charged_value=order_list[0].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Second Credit card",
        cc_brand="Brand2",
        cc_first_digits="1234",
        cc_last_digits="5678",
        cc_exp_month=12,
        cc_exp_year=2025,
        metadata={"foo": "baz"},
    )

    # third_transaction
    transaction_item_generator(
        order_id=order_list[1].pk,
        charged_value=order_list[1].total.gross.amount,
        payment_method_type="other",
        payment_method_name="Third payment method",
        cc_brand=None,
        cc_first_digits=None,
        cc_last_digits=None,
        cc_exp_month=None,
        cc_exp_year=None,
        metadata={"foo": "zaz"},
    )

    # fourth_transaction
    transaction_item_generator(
        order_id=order_list[2].pk,
        charged_value=order_list[2].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Fourth Credit card",
        cc_brand="Brand4",
        metadata={"foo": "bar"},
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"transactions": transaction_filters}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("address_filter", "expected_indexes"),
    [
        ({"phoneNumber": {"eq": "+48123456789"}}, [0]),
        ({"phoneNumber": {"eq": "+1987654321"}}, [1]),
        ({"phoneNumber": {"eq": "notfound"}}, []),
        ({"phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]}}, [0, 2]),
        ({"phoneNumber": {"oneOf": ["notfound"]}}, []),
        ({"country": {"eq": "GE"}}, [0]),
        ({"country": {"eq": "US"}}, [1]),
        ({"country": {"eq": "CN"}}, [2]),
        ({"country": {"eq": "JP"}}, []),
        ({"country": {"oneOf": ["GE", "CN"]}}, [0, 2]),
        ({"country": {"oneOf": ["JP"]}}, []),
        ({"country": {"notOneOf": ["GE", "CN", "PL"]}}, [1]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "GE"}}, [0]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "US"}}, []),
        (
            {
                "phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]},
                "country": {"notOneOf": ["GE"]},
            },
            [2],
        ),
        (None, []),
        ({"phoneNumber": {"eq": None}}, []),
        ({"phoneNumber": {"oneOf": []}}, []),
        ({"country": {"eq": None}}, []),
        ({"country": {"oneOf": []}}, []),
    ],
)
def test_orders_filter_by_billing_address(
    address_filter,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    phones = [
        "+48123456789",
        "+1987654321",
        "+86555555555",
    ]
    countries = ["GE", "US", "CN"]
    addresses = [
        Address.objects.create(
            first_name="John",
            last_name="Doe",
            company_name="Mirumee Software",
            street_address_1="Tęczowa 7",
            city="WROCŁAW",
            postal_code="53-601",
            country=country,
            phone=phone,
        )
        for phone, country in zip(phones, countries, strict=True)
    ]
    for order, address in zip(order_list, addresses, strict=True):
        order.billing_address = address
    Order.objects.bulk_update(order_list, ["billing_address"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"billingAddress": address_filter}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("address_filter", "expected_indexes"),
    [
        ({"phoneNumber": {"eq": "+48123456789"}}, [0]),
        ({"phoneNumber": {"eq": "+1987654321"}}, [1]),
        ({"phoneNumber": {"eq": "notfound"}}, []),
        ({"phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]}}, [0, 2]),
        ({"phoneNumber": {"oneOf": ["notfound"]}}, []),
        ({"country": {"eq": "GE"}}, [0]),
        ({"country": {"eq": "US"}}, [1]),
        ({"country": {"eq": "CN"}}, [2]),
        ({"country": {"eq": "JP"}}, []),
        ({"country": {"oneOf": ["GE", "CN"]}}, [0, 2]),
        ({"country": {"oneOf": ["JP"]}}, []),
        ({"country": {"notOneOf": ["GE", "CN", "PL"]}}, [1]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "GE"}}, [0]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "US"}}, []),
        (
            {
                "phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]},
                "country": {"notOneOf": ["GE"]},
            },
            [2],
        ),
        (None, []),
        ({"phoneNumber": {"eq": None}}, []),
        ({"phoneNumber": {"oneOf": []}}, []),
        ({"country": {"eq": None}}, []),
        ({"country": {"oneOf": []}}, []),
    ],
)
def test_orders_filter_by_shipping_address(
    address_filter,
    expected_indexes,
    order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    phones = [
        "+48123456789",
        "+1987654321",
        "+86555555555",
    ]
    countries = ["GE", "US", "CN"]
    addresses = [
        Address.objects.create(
            first_name="John",
            last_name="Doe",
            company_name="Mirumee Software",
            street_address_1="Tęczowa 7",
            city="WROCŁAW",
            postal_code="53-601",
            country=country,
            phone=phone,
        )
        for phone, country in zip(phones, countries, strict=True)
    ]
    for order, address in zip(order_list, addresses, strict=True):
        order.shipping_address = address
    Order.objects.bulk_update(order_list, ["shipping_address"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"shippingAddress": address_filter}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["orders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order_list[i].number) for i in expected_indexes}
