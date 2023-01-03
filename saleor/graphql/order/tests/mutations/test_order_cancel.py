from unittest.mock import ANY, patch

import graphene

from .....giftcard import GiftCardEvents
from .....giftcard.events import gift_cards_bought_event
from ....tests.utils import get_graphql_content

MUTATION_ORDER_CANCEL = """
mutation cancelOrder($id: ID!) {
    orderCancel(id: $id) {
        order {
            status
        }
        errors{
            field
            code
            message
        }
    }
}
"""


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_as_app(
    mock_clean_order_cancel,
    mock_cancel_order,
    app_api_client,
    permission_manage_orders,
    order_with_lines,
):
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = app_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=None, app=app_api_client.app, manager=ANY
    )


@patch("saleor.graphql.order.mutations.order_cancel.cancel_order")
@patch("saleor.graphql.order.mutations.order_cancel.clean_order_cancel")
def test_order_cancel_with_bought_gift_cards(
    mock_clean_order_cancel,
    mock_cancel_order,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    gift_card,
):
    order = order_with_lines
    mock_clean_order_cancel.return_value = order
    gift_cards_bought_event([gift_card], order, staff_api_client.user, None)
    assert gift_card.is_active is True
    order_id = graphene.Node.to_global_id("Order", order.id)
    variables = {"id": order_id}
    response = staff_api_client.post_graphql(
        MUTATION_ORDER_CANCEL, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderCancel"]
    assert not data["errors"]

    mock_clean_order_cancel.assert_called_once_with(order)
    mock_cancel_order.assert_called_once_with(
        order=order, user=staff_api_client.user, app=None, manager=ANY
    )

    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    assert gift_card.events.filter(type=GiftCardEvents.DEACTIVATED)
