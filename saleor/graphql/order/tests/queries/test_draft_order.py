import pytest

from .....order.models import Order
from ....tests.utils import assert_no_permission, get_graphql_content

DRAFT_ORDER_QUERY = """
    query DraftOrdersQuery {
        draftOrders(first: 10) {
            edges {
                node {
                    id
                    number
                }
            }
        }
    }
"""


@pytest.fixture
def draft_orders_in_different_channels(
    draft_order_list, channel_USD, channel_JPY, channel_PLN
):
    draft_order_list[0].channel = channel_USD
    draft_order_list[1].channel = channel_JPY
    draft_order_list[2].channel = channel_PLN

    Order.objects.bulk_update(draft_order_list, ["channel"])
    return draft_order_list


def test_draft_order_query(
    staff_api_client, permission_group_manage_orders, order, draft_order_list
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == Order.objects.drafts().count()


def test_query_draft_orders_by_user_with_access_to_all_channels(
    staff_api_client,
    permission_group_all_perms_all_channels,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_all_channels.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == len(draft_orders_in_different_channels)


def test_query_draft_orders_by_user_with_restricted_access_to_channels(
    staff_api_client,
    permission_group_all_perms_channel_USD_only,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_channel_USD_only.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    content = get_graphql_content(response)

    assert len(content["data"]["draftOrders"]["edges"]) == 1
    assert content["data"]["draftOrders"]["edges"][0]["node"]["number"] == str(
        draft_orders_in_different_channels[0].number
    )


def test_query_draft_orders_by_user_with_restricted_access_to_channels_no_acc_channels(
    staff_api_client,
    permission_group_all_perms_without_any_channel,
    draft_orders_in_different_channels,
):
    # given
    permission_group_all_perms_without_any_channel.user_set.add(staff_api_client.user)

    # when
    response = staff_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    content = get_graphql_content(response)
    assert len(content["data"]["draftOrders"]["edges"]) == 0


def test_query_draft_orders_by_app(
    app_api_client, permission_manage_orders, draft_orders_in_different_channels
):
    # when
    response = app_api_client.post_graphql(
        DRAFT_ORDER_QUERY, permissions=(permission_manage_orders,)
    )

    # then
    edges = get_graphql_content(response)["data"]["draftOrders"]["edges"]

    assert len(edges) == len(draft_orders_in_different_channels)


def test_query_draft_orders_by_customer(
    user_api_client, draft_orders_in_different_channels
):
    # when
    response = user_api_client.post_graphql(DRAFT_ORDER_QUERY)

    # then
    assert_no_permission(response)
