import datetime
from uuid import uuid4

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....core.postgres import FlatConcatSearchVector
from .....giftcard.events import gift_cards_bought_event, gift_cards_used_in_order_event
from .....order import OrderAuthorizeStatus, OrderChargeStatus, OrderStatus
from .....order.models import Order
from .....order.search import (
    prepare_order_search_vector_value,
)
from .....payment import ChargeStatus
from .....payment.models import Payment
from ....payment.enums import PaymentChargeStatusEnum
from ....tests.utils import get_graphql_content, get_graphql_content_from_response

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
                "range": {
                    "gte": (timezone.now() + datetime.timedelta(days=3)).isoformat(),
                    "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
                }
            },
            [1, 2],
        ),
        (
            {
                "range": {
                    "gte": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
                }
            },
            [1, 2],
        ),
        (
            {
                "range": {
                    "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
                }
            },
            [0, 1, 2],
        ),
        (
            {
                "range": {
                    "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
                }
            },
            [],
        ),
        (None, []),
        ({"range": {"gte": None}}, []),
        ({"range": {"lte": None}}, []),
        ({"range": {"lte": None, "gte": None}}, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
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
                "range": {
                    "gte": (timezone.now() + datetime.timedelta(days=3)).isoformat(),
                    "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
                }
            },
            [0, 1],
        ),
        (
            {
                "range": {
                    "gte": (timezone.now() + datetime.timedelta(days=5)).isoformat(),
                }
            },
            [0],
        ),
        (
            {
                "range": {
                    "lte": (timezone.now() + datetime.timedelta(days=25)).isoformat(),
                }
            },
            [0, 1, 2],
        ),
        (
            {
                "range": {
                    "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
                }
            },
            [],
        ),
        (None, []),
        ({"range": {"gte": None}}, []),
        ({"range": {"lte": None}}, []),
        ({"range": {"lte": None, "gte": None}}, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
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
        "where": {"number": {"eq": "123"}},
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
        ({"eq": PaymentChargeStatusEnum.NOT_CHARGED.name}, [0]),
        ({"oneOf": [PaymentChargeStatusEnum.CANCELLED.name]}, [1]),
        ({"oneOf": [PaymentChargeStatusEnum.FULLY_CHARGED.name]}, [2]),
        (
            {
                "oneOf": [
                    PaymentChargeStatusEnum.CANCELLED.name,
                    PaymentChargeStatusEnum.FULLY_CHARGED.name,
                ]
            },
            [1, 2],
        ),
        ({"eq": PaymentChargeStatusEnum.FULLY_REFUNDED.name}, []),
        ({}, []),
        ({"oneOf": []}, []),
        ({"eq": None}, []),
        (None, []),
    ],
)
def test_order_filter_by_payment_status(
    where,
    indexes,
    staff_api_client,
    order_list,
    payments_dummy,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    payments_dummy[0].order = order_list[0]
    payments_dummy[0].charge_status = ChargeStatus.NOT_CHARGED
    payments_dummy[1].order = order_list[1]
    payments_dummy[1].charge_status = ChargeStatus.CANCELLED
    payments_dummy[2].order = order_list[2]
    payments_dummy[2].charge_status = ChargeStatus.FULLY_CHARGED
    Payment.objects.bulk_update(payments_dummy, ["order", "charge_status"])
    variables = {
        "where": {"paymentStatus": where},
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


@freeze_time("2021-11-01 12:00:01")
def test_order_filter_is_preorder_true(
    staff_api_client,
    permission_group_manage_orders,
    preorders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isPreorder": True}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    assert len(returned_orders) == len(preorders)
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in preorders
    }


@freeze_time("2021-11-01 12:00:01")
def test_order_filter_is_preorder_false(
    staff_api_client,
    permission_group_manage_orders,
    preorders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isPreorder": False}}

    # when
    response = staff_api_client.post_graphql(ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["orders"]["edges"]
    expected_orders = Order.objects.exclude(
        id__in=[preorder.id for preorder in preorders]
    ).exclude(status=OrderStatus.DRAFT)
    expected_ids = {
        graphene.Node.to_global_id("Order", order.pk) for order in expected_orders
    }
    returned_ids = {order["node"]["id"] for order in returned_orders}
    assert returned_ids == expected_ids


@freeze_time("2021-11-01 12:00:01")
def test_order_filter_is_preorder_none(
    staff_api_client,
    permission_group_manage_orders,
    preorders,
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isPreorder": None}}

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
