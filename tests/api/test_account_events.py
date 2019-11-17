import graphene
from django.db import models

from saleor.account import events as account_events
from saleor.account.models import User

from .utils import get_graphql_content

QUERY_CUSTOMER_EVENTS = """
query customerEvents($customerId: ID!) {
  user(id: $customerId) {
    id
    events {
      id
      type
      user {
        id
      }
      message
      count
      order {
        id
      }
      orderLine {
        id
      }
    }
  }
}
"""


def test_account_events_are_properly_restricted(
    staff_api_client, permission_manage_staff, staff_user
):
    """Ensure that retrieve events of a customer is properly restricted."""

    # Retrieve the staff user's id
    customer_id = graphene.Node.to_global_id("User", staff_user.id)

    # Test both with and without proper permissions
    content = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={"customerId": customer_id},
            permissions=[permission_manage_staff],
        )
    )["data"]["user"]

    # Ensure the correct data is returned when the request is valid
    assert content["id"] == customer_id
    assert content["events"] == []


def _model_to_node_id(instance: models.Model) -> str:
    return graphene.Node.to_global_id(instance.__class__.__name__, instance.pk)


def _get_event_from_graphql(staff_api_client, requested_user: User, permission) -> dict:

    staff_api_client.user.user_permissions.add(permission)
    received_events = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={
                "customerId": graphene.Node.to_global_id("User", requested_user.id)
            },
        )
    )["data"]["user"]["events"]

    # Ensure the correct count of events was returned
    assert len(received_events) == 1, "The expected event was not returned"
    return received_events[0]


def test_account_event_customer_account_was_created(
    staff_api_client, customer_user, permission_manage_users
):
    event = account_events.customer_account_created_event(user=customer_user)
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": None,
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.ACCOUNT_CREATED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_sent_password_reset_email_to_customer_event(
    staff_api_client, customer_user, permission_manage_users
):
    event = account_events.customer_password_reset_link_sent_event(
        user_id=customer_user.pk
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": None,
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.PASSWORD_RESET_LINK_SENT.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_customer_reset_password_from_link_event(
    staff_api_client, customer_user, permission_manage_users
):
    event = account_events.customer_password_reset_event(user=customer_user)
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": None,
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.PASSWORD_RESET.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_customer_placed_order_event_resolves_properly(
    staff_api_client, customer_user, order_line, permission_manage_users
):
    order = order_line.order
    event = account_events.customer_placed_order_event(user=customer_user, order=order)
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": None,
        "order": {"id": _model_to_node_id(order)},
        "orderLine": None,
        "type": account_events.CustomerEvents.PLACED_ORDER.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_customer_added_to_note_order_event_resolves_properly(
    staff_api_client, customer_user, order_line, permission_manage_users
):
    order = order_line.order
    event = account_events.customer_added_to_note_order_event(
        user=customer_user, order=order, message="418 - I'm a teapot."
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": "418 - I'm a teapot.",
        "order": {"id": _model_to_node_id(order)},
        "orderLine": None,
        "type": account_events.CustomerEvents.NOTE_ADDED_TO_ORDER.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_customer_downloaded_a_digital_link_event_resolves_properly(
    staff_api_client, customer_user, order_line, permission_manage_users
):
    order = order_line.order
    event = account_events.customer_downloaded_a_digital_link_event(
        user=customer_user, order_line=order_line
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(customer_user)},
        "count": None,
        "message": None,
        "order": {"id": _model_to_node_id(order)},
        "orderLine": {"id": _model_to_node_id(order_line)},
        "type": account_events.CustomerEvents.DIGITAL_LINK_DOWNLOADED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, customer_user, permission_manage_users
    )

    assert expected_data == received_data


def test_account_event_staff_user_deleted_a_customer_event_resolves_properly(
    staff_api_client, staff_user, permission_manage_staff
):
    event = account_events.staff_user_deleted_a_customer_event(
        staff_user=staff_user, deleted_count=123
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(staff_user)},
        "count": 123,
        "message": None,
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.CUSTOMER_DELETED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, staff_user, permission_manage_staff
    )

    assert expected_data == received_data


def test_account_invalid_or_deleted_order_line_return_null(
    staff_api_client, permission_manage_users, customer_user, order_line
):
    """Ensure getting an order line does return null if it is no longer existing,
    despite the fact it *shouldn't* happen in production."""

    # Prepare test
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # Create the event
    account_events.customer_downloaded_a_digital_link_event(
        user=customer_user, order_line=order_line
    )

    # Delete the line
    order_line.delete()

    # Retrieve it
    received_customer_events = get_graphql_content(
        staff_api_client.post_graphql(
            """
            query customerEvents($customerId: ID!) {
              user(id: $customerId) {
                id
                events {
                  orderLine {
                    id
                  }
                }
              }
            }
            """,
            variables={
                "customerId": graphene.Node.to_global_id("User", customer_user.id)
            },
        )
    )["data"]["user"]["events"]

    # Ensure the data is valid
    assert received_customer_events == [{"orderLine": None}]


def test_account_event_staff_user_assigned_new_name_to_customer_event_resolves_properly(
    staff_api_client, staff_user, permission_manage_staff
):
    event = account_events.staff_user_assigned_name_to_a_customer_event(
        staff_user=staff_user, new_name="Hello World!"
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(staff_user)},
        "count": None,
        "message": "Hello World!",
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.NAME_ASSIGNED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, staff_user, permission_manage_staff
    )

    assert expected_data == received_data


def test_account_event_staff_user_assigned_email_to_customer_event_resolves_properly(
    staff_api_client, staff_user, permission_manage_staff
):
    event = account_events.staff_user_assigned_email_to_a_customer_event(
        staff_user=staff_user, new_email="hello@example.com"
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(staff_user)},
        "count": None,
        "message": "hello@example.com",
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.EMAIL_ASSIGNED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, staff_user, permission_manage_staff
    )

    assert expected_data == received_data


def test_account_event_staff_user_added_note_to_customer_event_resolves_properly(
    staff_api_client, staff_user, permission_manage_staff
):
    event = account_events.staff_user_added_note_to_a_customer_event(
        staff_user=staff_user, note="New note's content!"
    )
    expected_data = {
        "id": _model_to_node_id(event),
        "user": {"id": _model_to_node_id(staff_user)},
        "count": None,
        "message": "New note's content!",
        "order": None,
        "orderLine": None,
        "type": account_events.CustomerEvents.NOTE_ADDED.upper(),
    }

    received_data = _get_event_from_graphql(
        staff_api_client, staff_user, permission_manage_staff
    )

    assert expected_data == received_data
