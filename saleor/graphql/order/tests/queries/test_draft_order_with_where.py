import datetime

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import Address
from .....order import (
    OrderAuthorizeStatus,
    OrderChargeStatus,
    OrderEvents,
    OrderStatus,
)
from .....order.models import Order, OrderEvent, OrderLine
from ....tests.utils import get_graphql_content, get_graphql_content_from_response


def test_order_query_with_filter_and_where(
    staff_api_client,
    permission_group_manage_orders,
    orders,
    draft_order,
):
    # given
    query = """
        query ($where: DraftOrderWhereInput!, $filter: OrderDraftFilterInput!) {
            draftOrders(first: 10, where: $where, filter: $filter) {
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
            "number": {
                "eq": draft_order.number,
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
    assert not content["data"]["draftOrders"]


DRAFT_ORDERS_WHERE_QUERY = """
    query($where: DraftOrderWhereInput!) {
      draftOrders(first: 10, where: $where) {
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


def test_draft_order_filter_by_ids(
    staff_api_client, permission_group_manage_orders, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    ids = [
        graphene.Node.to_global_id("Order", order.pk) for order in draft_order_list[:2]
    ]
    variables = {"where": {"ids": ids}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(draft_order_list[0].number),
        str(draft_order_list[1].number),
    }


def test_draft_order_filter_by_none_as_ids(
    staff_api_client, permission_group_manage_orders, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"ids": None}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_order_filter_by_ids_empty_list(
    staff_api_client, permission_group_manage_orders, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"ids": []}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=10)).isoformat(),
                "lte": (timezone.now() - datetime.timedelta(days=3)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=3)).isoformat(),
            },
            [0],
        ),
        (
            {
                "lte": (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            },
            [0, 1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=15)).isoformat(),
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
def test_draft_orders_filter_by_created_at(
    where,
    indexes,
    draft_order,
    order_generator,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    with freeze_time((timezone.now() - datetime.timedelta(days=5)).isoformat()):
        order_2 = order_generator(status=OrderStatus.DRAFT)

    with freeze_time((timezone.now() - datetime.timedelta(days=10)).isoformat()):
        order_3 = order_generator(status=OrderStatus.DRAFT)

    order_list = [draft_order, order_2, order_3]

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"createdAt": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
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
def test_draft_orders_filter_by_updated_at(
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].updated_at = timezone.now() + datetime.timedelta(days=15)
    draft_order_list[1].updated_at = timezone.now() + datetime.timedelta(days=3)
    draft_order_list[2].updated_at = timezone.now() + datetime.timedelta(days=1)
    Order.objects.bulk_update(draft_order_list, ["updated_at"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"updatedAt": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


def test_draft_order_filter_by_users(
    staff_api_client, permission_group_manage_orders, draft_order_list, user_list
):
    # given
    draft_order_list[0].user = user_list[0]
    draft_order_list[1].user = user_list[1]
    draft_order_list[2].user = user_list[2]
    Order.objects.bulk_update(draft_order_list, ["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    user_ids = [graphene.Node.to_global_id("User", user.pk) for user in user_list[:2]]
    variables = {
        "where": {"user": {"oneOf": user_ids}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(draft_order_list[0].number),
        str(draft_order_list[1].number),
    }


def test_draft_order_filter_by_user(
    staff_api_client, permission_group_manage_orders, draft_order_list, user_list
):
    # given
    draft_order_list[0].user = user_list[0]
    draft_order_list[0].save(update_fields=["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    user_id = graphene.Node.to_global_id("User", user_list[0].pk)

    variables = {
        "where": {"user": {"eq": user_id}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 1
    assert str(draft_order_list[0].number) == orders[0]["node"]["number"]


def test_draft_order_filter_by_none_as_user(
    staff_api_client, permission_group_manage_orders, draft_order_list, user_list
):
    # given
    draft_order_list[0].user = user_list[0]
    draft_order_list[0].save(update_fields=["user"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"user": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_order_filter_by_user_email(
    staff_api_client, permission_group_manage_orders, draft_order_list, user_list
):
    # given
    draft_order_list[1].user_email = user_list[0].email
    draft_order_list[1].save(update_fields=["user_email"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"userEmail": {"eq": user_list[0].email}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 1
    assert str(draft_order_list[1].number) == orders[0]["node"]["number"]


def test_draft_order_filter_by_none_as_user_email(
    staff_api_client, permission_group_manage_orders, draft_order_list, user_list
):
    # given
    draft_order_list[0].user_email = user_list[0].email
    draft_order_list[0].save(update_fields=["user_email"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"userEmail": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_order_filter_by_numbers_range(
    staff_api_client, permission_group_manage_orders, draft_order_list
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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(draft_order_list[0].number),
        str(draft_order_list[1].number),
    }


def test_draft_order_filter_by_number(
    staff_api_client, permission_group_manage_orders, draft_order_list, draft_order
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": draft_order.number}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 1
    assert str(draft_order.number) == orders[0]["node"]["number"]


def test_draft_order_filter_by_none_as_number(
    staff_api_client, permission_group_manage_orders, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": None}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_order_filter_by_number_nothing_returned(
    staff_api_client, permission_group_manage_orders, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {"number": {"eq": "999"}},
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_order_filter_by_channel_id(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    channel_USD,
    channel_PLN,
):
    # given
    draft_order_list[0].channel = channel_USD
    draft_order_list[1].channel = channel_PLN
    draft_order_list[2].channel = channel_USD
    Order.objects.bulk_update(draft_order_list, ["channel"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {
        "where": {
            "channelId": {"eq": graphene.Node.to_global_id("Channel", channel_USD.id)}
        }
    }

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 2
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[0].number), str(draft_order_list[2].number)}


def test_draft_order_filter_by_channel_ids(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    channel_USD,
    channel_PLN,
):
    # given
    draft_order_list[0].channel = channel_USD
    draft_order_list[1].channel = channel_PLN
    draft_order_list[2].channel = channel_USD
    Order.objects.bulk_update(draft_order_list, ["channel"])

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

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
    assert len(orders) == 3
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {
        str(draft_order_list[0].number),
        str(draft_order_list[1].number),
        str(draft_order_list[2].number),
    }


def test_draft_order_filter_by_channel_id_none(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    channel_USD,
    channel_PLN,
):
    # given
    draft_order_list[0].channel = channel_USD
    draft_order_list[1].channel = channel_PLN
    draft_order_list[2].channel = channel_USD
    Order.objects.bulk_update(draft_order_list, ["channel"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {"where": {"channelId": {"eq": None}}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)
    data = get_graphql_content(response)
    orders = data["data"]["draftOrders"]["edges"]
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
def test_draft_orders_filter_by_authorize_status(
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].authorize_status = OrderAuthorizeStatus.FULL
    draft_order_list[1].authorize_status = OrderAuthorizeStatus.PARTIAL
    draft_order_list[2].authorize_status = OrderAuthorizeStatus.NONE
    Order.objects.bulk_update(draft_order_list, ["authorize_status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"authorizeStatus": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


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
def test_draft_orders_filter_by_charge_status(
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].charge_status = OrderChargeStatus.OVERCHARGED
    draft_order_list[1].charge_status = OrderChargeStatus.PARTIAL
    draft_order_list[2].charge_status = OrderChargeStatus.NONE
    Order.objects.bulk_update(draft_order_list, ["charge_status"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"chargeStatus": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


def test_draft_order_filter_is_click_and_collect_true(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    warehouse_for_cc,
):
    # given
    order_1 = draft_order_list[0]
    order_1.collection_point = warehouse_for_cc
    order_1.collection_point_name = warehouse_for_cc.name

    order_2 = draft_order_list[1]
    order_2.collection_point_name = warehouse_for_cc.name
    Order.objects.bulk_update(
        [order_1, order_2], ["collection_point", "collection_point_name"]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isClickAndCollect": True}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["draftOrders"]["edges"]
    assert len(returned_orders) == 2
    assert {order["node"]["id"] for order in returned_orders} == {
        graphene.Node.to_global_id("Order", order.pk) for order in [order_1, order_2]
    }


def test_draft_order_filter_is_click_and_collect_false(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    warehouse_for_cc,
):
    # given
    order_1 = draft_order_list[0]
    order_1.collection_point = warehouse_for_cc
    order_1.collection_point_name = warehouse_for_cc.name

    order_2 = draft_order_list[1]
    order_2.collection_point = warehouse_for_cc
    Order.objects.bulk_update(
        [order_1, order_2], ["collection_point", "collection_point_name"]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isClickAndCollect": False}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["draftOrders"]["edges"]
    assert len(returned_orders) == 1
    assert returned_orders[0]["node"]["id"] == (
        graphene.Node.to_global_id("Order", draft_order_list[2].pk)
    )


def test_draft_order_filter_is_click_and_collect_none(
    staff_api_client,
    permission_group_manage_orders,
    draft_order_list,
    warehouse_for_cc,
):
    # given
    order_1 = draft_order_list[0]
    order_1.collection_point = warehouse_for_cc
    order_1.collection_point_name = warehouse_for_cc.name

    order_2 = draft_order_list[1]
    order_2.collection_point = warehouse_for_cc
    Order.objects.bulk_update(
        [order_1, order_2], ["collection_point", "collection_point_name"]
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"isClickAndCollect": None}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    returned_orders = content["data"]["draftOrders"]["edges"]
    assert len(returned_orders) == 0


def test_draft_order_filter_by_voucher_code_eq(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    draft_order_list[0].voucher_code = codes[0].code
    draft_order_list[1].voucher_code = codes[1].code
    draft_order_list[1].voucher = voucher_with_many_codes
    draft_order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(draft_order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": {"eq": codes[0].code}}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 1
    assert orders[0]["node"]["number"] == str(draft_order_list[0].number)


def test_draft_order_filter_by_voucher_code_one_of(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    draft_order_list[0].voucher_code = codes[0].code
    draft_order_list[1].voucher_code = codes[1].code
    draft_order_list[1].voucher = voucher_with_many_codes
    draft_order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(draft_order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": {"oneOf": [codes[1].code, codes[2].code]}}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 2
    returned_numbers = {node["node"]["number"] for node in orders}
    assert returned_numbers == {
        str(draft_order_list[1].number),
        str(draft_order_list[2].number),
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
def test_draft_order_filter_by_voucher_code_empty_value(
    where,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
    voucher_with_many_codes,
):
    # given
    codes = voucher_with_many_codes.codes.all()
    draft_order_list[0].voucher_code = codes[0].code
    draft_order_list[1].voucher_code = codes[1].code
    draft_order_list[1].voucher = voucher_with_many_codes
    draft_order_list[2].voucher_code = codes[2].code
    Order.objects.bulk_update(draft_order_list, ["voucher_code", "voucher"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"voucherCode": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


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
def test_draft_orders_filter_by_lines_metadata(
    metadata,
    expected_indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    metadata_values = [
        {"foo": "bar"},
        {"foo": "zaz"},
        {},
    ]
    for order, metadata_value in zip(draft_order_list, metadata_values, strict=True):
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
    variables = {"where": {"lines": {"metadata": metadata}}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}


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
def test_draft_orders_filter_by_lines_count(
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].lines_count = 1
    draft_order_list[1].lines_count = 2
    draft_order_list[2].lines_count = 3
    Order.objects.bulk_update(draft_order_list, ["lines_count"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"linesCount": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


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
def test_draft_orders_filter_by_total_gross(
    currency,
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].total_gross_amount = "110.00"
    draft_order_list[0].currency = "USD"
    draft_order_list[1].total_gross_amount = "150.00"
    draft_order_list[1].currency = "USD"
    draft_order_list[2].total_gross_amount = "200.00"
    draft_order_list[2].currency = "PLN"
    Order.objects.bulk_update(draft_order_list, ["total_gross_amount", "currency"])

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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


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
def test_draft_orders_filter_by_total_net(
    currency,
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].total_net_amount = "110.00"
    draft_order_list[0].currency = "USD"
    draft_order_list[1].total_net_amount = "150.00"
    draft_order_list[1].currency = "USD"
    draft_order_list[2].total_net_amount = "200.00"
    draft_order_list[2].currency = "PLN"
    Order.objects.bulk_update(draft_order_list, ["total_net_amount", "currency"])

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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


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
def test_draft_orders_filter_by_metadata(
    metadata,
    expected_indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    draft_order_list[0].metadata = {"foo": "bar"}
    draft_order_list[1].metadata = {"foo": "zaz"}
    draft_order_list[2].metadata = {}
    Order.objects.bulk_update(draft_order_list, ["metadata"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}


def test_draft_orders_filter_by_product_type_id(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(draft_order_list, product_type_ids, strict=True):
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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 1
    assert str(draft_order_list[1].number) == orders[0]["node"]["number"]


def test_draft_orders_filter_by_product_type_ids(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(draft_order_list, product_type_ids, strict=True):
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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(draft_order_list[:2])
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(order.number) for order in draft_order_list[:2]}


def test_draft_orders_filter_by_product_type_ids_nothing_match(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(draft_order_list, product_type_ids, strict=True):
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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


def test_draft_orders_filter_by_product_type_none(
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    lines = []
    product_type_ids = [3, 4, 5]
    for order, product_type_id in zip(draft_order_list, product_type_ids, strict=True):
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
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == 0


@pytest.mark.parametrize(
    ("event_input", "expected_indexes"),
    [
        (
            {
                "date": {"gte": "2025-01-01T00:00:00Z"},
                "type": {"eq": OrderEvents.NOTE_ADDED.upper()},
            },
            [0, 1, 2],
        ),
        (
            {
                "date": {"gte": "2025-01-01T00:00:00Z"},
                "type": {"eq": OrderEvents.ORDER_FULLY_PAID.upper()},
            },
            [0, 1],
        ),
        (
            {
                "date": {"gte": "2026-01-01T00:00:00Z"},
            },
            [],
        ),
        (
            {
                "date": {"gte": "2020-01-01T00:00:00Z"},
            },
            [0, 1, 2],
        ),
        (
            {
                "type": {
                    "oneOf": [
                        OrderEvents.NOTE_ADDED.upper(),
                        OrderEvents.ORDER_FULLY_PAID.upper(),
                    ]
                },
            },
            [0, 1, 2],
        ),
    ],
)
def test_draft_orders_filter_by_order_events(
    event_input,
    expected_indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    with freeze_time("2025-01-01T00:00:00Z"):
        OrderEvent.objects.bulk_create(
            [
                OrderEvent(order=order, type=OrderEvents.NOTE_ADDED)
                for order in draft_order_list
            ]
        )

    with freeze_time("2025-02-02T00:00:00Z"):
        OrderEvent.objects.bulk_create(
            [
                OrderEvent(order=order, type=OrderEvents.ORDER_FULLY_PAID)
                for order in draft_order_list[:2]
            ]
        )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"events": event_input}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "paymentMethodDetails": {
                    "type": {"eq": "CARD"},
                }
            },
            [0, 2],
        ),
        (
            {
                "paymentMethodDetails": {
                    "type": {"eq": "OTHER"},
                }
            },
            [1],
        ),
        (
            {
                "paymentMethodDetails": {
                    "card": {
                        "brand": {"eq": "Brand"},
                    }
                }
            },
            [0],
        ),
        (
            {
                "paymentMethodDetails": {
                    "card": {
                        "brand": {"eq": "Brand4"},
                    }
                }
            },
            [2],
        ),
        (
            {
                "paymentMethodDetails": {
                    "card": {
                        "brand": {"eq": "Brand2"},
                    }
                }
            },
            [0],
        ),
        (
            {
                "paymentMethodDetails": {
                    "type": {"oneOf": ["CARD", "OTHER"]},
                }
            },
            [0, 1, 2],
        ),
        (
            {
                "paymentMethodDetails": {
                    "card": {
                        "brand": {"oneOf": ["Brand2", "Brand4"]},
                    }
                }
            },
            [0, 2],
        ),
    ],
)
def test_draft_orders_filter_by_transaction_payment_details(
    where,
    indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
    transaction_item_generator,
):
    # given
    # first_transaction
    transaction_item_generator(
        order_id=draft_order_list[0].pk,
        charged_value=draft_order_list[0].total.gross.amount,
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
        order_id=draft_order_list[0].pk,
        charged_value=draft_order_list[0].total.gross.amount,
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
        order_id=draft_order_list[1].pk,
        charged_value=draft_order_list[1].total.gross.amount,
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
        order_id=draft_order_list[2].pk,
        charged_value=draft_order_list[2].total.gross.amount,
        payment_method_type="card",
        payment_method_name="Fourth Credit card",
        cc_brand="Brand4",
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"transactions": where}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[index].number) for index in indexes}


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
def test_draft_orders_filter_by_transaction_metadata(
    metadata,
    expected_indexes,
    draft_order_list,
    staff_api_client,
    permission_group_manage_orders,
    transaction_item_generator,
):
    # given
    transaction_item_generator(
        order_id=draft_order_list[0].pk,
        charged_value=draft_order_list[0].total.gross.amount,
        metadata={"foo": "bar"},
    )

    transaction_item_generator(
        order_id=draft_order_list[0].pk,
        charged_value=draft_order_list[0].total.gross.amount,
        metadata={},
    )

    transaction_item_generator(
        order_id=draft_order_list[1].pk,
        charged_value=draft_order_list[1].total.gross.amount,
        metadata={"foo": "zaz"},
    )

    transaction_item_generator(
        order_id=draft_order_list[2].pk,
        charged_value=draft_order_list[2].total.gross.amount,
        metadata={},
    )

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"transactions": {"metadata": metadata}}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}


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
def test_draft_orders_filter_by_billing_address(
    address_filter,
    expected_indexes,
    draft_order_list,
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
    for order, address in zip(draft_order_list, addresses, strict=True):
        order.billing_address = address
    Order.objects.bulk_update(draft_order_list, ["billing_address"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"billingAddress": address_filter}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}


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
def test_draft_orders_filter_by_shipping_address(
    address_filter,
    expected_indexes,
    draft_order_list,
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
    for order, address in zip(draft_order_list, addresses, strict=True):
        order.shipping_address = address
    Order.objects.bulk_update(draft_order_list, ["shipping_address"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)
    variables = {"where": {"shippingAddress": address_filter}}

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDERS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    orders = content["data"]["draftOrders"]["edges"]
    assert len(orders) == len(expected_indexes)
    numbers = {node["node"]["number"] for node in orders}
    assert numbers == {str(draft_order_list[i].number) for i in expected_indexes}
