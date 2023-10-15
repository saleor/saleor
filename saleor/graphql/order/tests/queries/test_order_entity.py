import graphene

from .....order import OrderStatus
from .....order.models import Order
from ....tests.utils import get_graphql_content

ORDER_FEDERATION_QUERY = """
  query GetOrderInFederation($representations: [_Any]) {
    _entities(representations: $representations) {
      __typename
      ... on Order {
        id
        number
      }
    }
  }
"""


def test_staff_query_order_by_id_for_federation(
    staff_api_client, fulfilled_order, permission_group_manage_orders
):
    # given
    permission_group_manage_orders.user_set.add(staff_api_client.user)
    order_id = graphene.Node.to_global_id("Order", fulfilled_order.id)
    variables = {
        "representations": [
            {
                "__typename": "Order",
                "id": order_id,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        ORDER_FEDERATION_QUERY,
        variables,
        check_no_permissions=False,
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "Order",
            "id": order_id,
            "number": str(fulfilled_order.number),
        },
    ]


def test_staff_query_order_by_id_without_permission_for_federation(
    staff_api_client, fulfilled_order
):
    fulfilled_order_id = graphene.Node.to_global_id("Order", fulfilled_order.id)
    variables = {
        "representations": [
            {
                "__typename": "Order",
                "id": fulfilled_order_id,
            },
        ],
    }

    response = staff_api_client.post_graphql(ORDER_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_customer_query_own_orders_for_federation(
    user_api_client, customer_user, order_list
):
    order_unfulfilled = order_list[0]
    order_unfulfilled.user = customer_user

    order_unconfirmed = order_list[1]
    order_unconfirmed.status = OrderStatus.UNCONFIRMED
    order_unconfirmed.user = customer_user

    order_draft = order_list[2]
    order_draft.status = OrderStatus.DRAFT
    order_draft.user = customer_user

    Order.objects.bulk_update(
        [order_unconfirmed, order_draft, order_unfulfilled], ["user", "status"]
    )

    order_unfulfilled_id = graphene.Node.to_global_id("Order", order_unfulfilled.id)
    order_unconfirmed_id = graphene.Node.to_global_id("Order", order_unconfirmed.id)
    order_draft_id = graphene.Node.to_global_id("Order", order_draft.id)
    variables = {
        "representations": [
            {
                "__typename": "Order",
                "id": order_unfulfilled_id,
            },
            {
                "__typename": "Order",
                "id": order_unconfirmed_id,
            },
            {
                "__typename": "Order",
                "id": order_draft_id,
            },
        ],
    }

    response = user_api_client.post_graphql(
        ORDER_FEDERATION_QUERY,
        variables,
    )
    content = get_graphql_content(response)

    assert content["data"]["_entities"] == [
        {
            "__typename": "Order",
            "id": order_unfulfilled_id,
            "number": str(order_unfulfilled.number),
        },
        {
            "__typename": "Order",
            "id": order_unconfirmed_id,
            "number": str(order_unconfirmed.number),
        },
        # Users without permission cannot see draft orders
        None,
    ]


def test_customer_query_order_without_permission_for_federation(
    user2_api_client, fulfilled_order
):
    fulfilled_order_id = graphene.Node.to_global_id("Order", fulfilled_order.id)
    variables = {
        "representations": [
            {
                "__typename": "Order",
                "id": fulfilled_order_id,
            },
        ],
    }

    response = user2_api_client.post_graphql(ORDER_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_unauthenticated_query_order_for_federation(api_client, fulfilled_order):
    fulfilled_order_id = graphene.Node.to_global_id("Order", fulfilled_order.id)
    variables = {
        "representations": [
            {
                "__typename": "Order",
                "id": fulfilled_order_id,
            },
        ],
    }

    response = api_client.post_graphql(ORDER_FEDERATION_QUERY, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]
