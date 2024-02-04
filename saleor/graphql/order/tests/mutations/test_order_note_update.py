from unittest.mock import patch

import graphene
import pytest

from .....account.models import CustomerEvent
from .....order import OrderEvents, OrderStatus
from .....order.error_codes import OrderNoteUpdateErrorCode
from .....order.models import OrderEvent
from ....tests.utils import assert_no_permission, get_graphql_content

ORDER_NOTE_UPDATE_MUTATION = """
    mutation updateNote($id: ID!, $message: String!) {
        orderNoteUpdate(note: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            order {
                id
            }
            event {
                id
                user {
                    email
                }
                message
                related {
                    id
                    message
                }
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_update_as_staff_user(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order,
    staff_user,
):
    # given
    parameters = {"message": "a note"}
    note = OrderEvent.objects.create(
        order=order,
        type=OrderEvents.NOTE_ADDED,
        user=staff_user,
        parameters=parameters,
    )
    note_id = graphene.Node.to_global_id("OrderEvent", note.pk)
    order_id = graphene.Node.to_global_id("Order", order.id)

    message = "nuclear note"
    variables = {"id": note_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        ORDER_NOTE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteUpdate"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message
    assert data["event"]["related"]["id"] == note_id
    order_updated_webhook_mock.assert_called_once_with(order)

    order.refresh_from_db()
    assert order.status == OrderStatus.UNFULFILLED

    assert OrderEvent.objects.filter(order=order).count() == 2
    new_note = OrderEvent.objects.filter(order=order).exclude(pk=note.pk).get()
    assert new_note.type == OrderEvents.NOTE_UPDATED
    assert new_note.user == staff_user
    assert new_note.parameters == {"message": message}

    # Ensure no customer events were created as it was a staff action
    assert not CustomerEvent.objects.exists()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_update_as_app(
    order_updated_webhook_mock,
    app_api_client,
    permission_manage_orders,
    order,
    app,
):
    # given
    parameters = {"message": "a note"}
    note = OrderEvent.objects.create(
        order=order,
        type=OrderEvents.NOTE_ADDED,
        parameters=parameters,
    )
    note_id = graphene.Node.to_global_id("OrderEvent", note.pk)
    order_id = graphene.Node.to_global_id("Order", order.id)

    message = "nuclear note"
    variables = {"id": note_id, "message": message}

    # when
    response = app_api_client.post_graphql(
        ORDER_NOTE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteUpdate"]

    assert data["order"]["id"] == order_id
    assert data["event"]["user"] is None
    assert data["event"]["related"]["id"] == note_id
    order_updated_webhook_mock.assert_called_once_with(order)

    new_note = OrderEvent.objects.filter(order=order).exclude(pk=note.pk).get()
    assert new_note.type == OrderEvents.NOTE_UPDATED
    assert new_note.app == app
    assert not new_note.user


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_update_fail_on_empty_message(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order,
    message,
):
    # given
    note = OrderEvent.objects.create(
        order=order,
        type=OrderEvents.NOTE_ADDED,
    )
    note_id = graphene.Node.to_global_id("OrderEvent", note.pk)
    variables = {"id": note_id, "message": message}

    # when
    response = staff_api_client.post_graphql(
        ORDER_NOTE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteUpdate"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == OrderNoteUpdateErrorCode.REQUIRED.name
    order_updated_webhook_mock.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.order_updated")
def test_order_note_update_fail_on_wrong_id(
    order_updated_webhook_mock,
    staff_api_client,
    permission_manage_orders,
    order,
):
    # given
    note = OrderEvent.objects.create(
        order=order,
        type=OrderEvents.UPDATED_ADDRESS,  # add different event type than NOTE_ADDED
    )
    note_id = graphene.Node.to_global_id("OrderEvent", note.pk)
    variables = {"id": note_id, "message": "test"}

    # when
    response = staff_api_client.post_graphql(
        ORDER_NOTE_UPDATE_MUTATION, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["orderNoteUpdate"]
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == OrderNoteUpdateErrorCode.NOT_FOUND.name
    order_updated_webhook_mock.assert_not_called()


def test_order_note_remove_fail_on_missing_permission(staff_api_client, order):
    # given
    note = OrderEvent.objects.create(order=order, type=OrderEvents.NOTE_ADDED)
    note_id = graphene.Node.to_global_id("OrderEvent", note.pk)
    variables = {"id": note_id, "message": "test"}

    # when
    response = staff_api_client.post_graphql(ORDER_NOTE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)
