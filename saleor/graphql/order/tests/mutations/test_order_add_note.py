from unittest.mock import patch

import graphene
import pytest

from .....account.models import CustomerEvent
from .....order import OrderStatus
from .....order import events as order_events
from .....order.error_codes import OrderErrorCode
from ....tests.utils import get_graphql_content

ORDER_ADD_NOTE_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        orderAddNote(order: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                user {
                    email
                }
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_as_staff_user(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    staff_user,
):
    """We are testing that adding a note to an order as a staff user is doing the
    expected behaviors."""
    order = order_with_lines
    assert not order.events.all()
    order_id = graphene.Node.to_global_id("Order", order.id)
    message = "nuclear note"
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message
    order_updated_webhook_mock.assert_called_once_with(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    # Ensure the correct order event was created
    event = order.events.get()
    assert event.type == order_events.OrderEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}

    # Ensure not customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@pytest.mark.parametrize(
    "message",
    (
        "",
        "   ",
    ),
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_add_note_fail_on_empty_message(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
    message,
):
    order_id = graphene.Node.to_global_id("Order", order_with_lines.id)
    variables = {"id": order_id, "message": message}
    response = staff_api_client.post_graphql(
        ORDER_ADD_NOTE_MUTATION, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["orderAddNote"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == OrderErrorCode.REQUIRED.name
    order_updated_webhook_mock.assert_not_called()
