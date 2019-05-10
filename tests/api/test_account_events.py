import graphene

from saleor.account import events as account_events

from ..checks import events as events_checks
from .utils import get_graphql_content

QUERY_CUSTOMER_EVENTS = """
query customerEvents($customerId: ID!) {
  user(id: $customerId) {
    id
    events {
      id
      type
      date
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
    staff_api_client, permission_manage_users, staff_user
):
    """Ensure that retrieve events of a customer is properly restricted."""

    # Retrieve the staff user's id
    customer_id = graphene.Node.to_global_id("User", staff_user.id)

    # Test both with and without proper permissions
    content = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={"customerId": customer_id},
            permissions=[permission_manage_users],
        )
    )["data"]["user"]

    # Ensure the correct data is returned when the request is valid
    assert content["id"] == customer_id
    assert content["events"] == []


def test_account_events_resolve_properly(
    staff_api_client, staff_user, customer_user, order_line, permission_manage_users
):
    """Create every possible event and attempt to resolve them and
    check if they properly returned all the expected data."""

    # Prepare test
    staff_api_client.user.user_permissions.add(permission_manage_users)
    expected_event_count = len(account_events.CustomerEvents.CHOICES)

    # Create every event
    placed_order_event = account_events.customer_placed_order_event(
        user=customer_user, order=order_line.order
    )
    note_added_event = account_events.customer_added_to_note_order_event(
        user=customer_user, order=order_line.order, message="418 - I'm a teapot."
    )
    download_event = account_events.customer_downloaded_a_digital_link_event(
        user=customer_user, order_line=order_line
    )
    customer_deleted_event = account_events.staff_user_deleted_a_customer_event(
        staff_user=staff_user, deleted_count=123
    )

    # Test data
    customer_events = [placed_order_event, note_added_event, download_event]
    staff_events = [customer_deleted_event]

    # Ensure all events were created and *will* be tested properly by the maintainers
    assert account_events.CustomerEvent.objects.count() == expected_event_count, (
        "Not all events were created or were improperly created. "
        "Please ensure you test them all."
    )

    # Retrieve the events
    received_customer_events = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={
                "customerId": graphene.Node.to_global_id("User", customer_user.id)
            },
        )
    )["data"]["user"]["events"]
    received_staff_events = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={"customerId": graphene.Node.to_global_id("User", staff_user.id)},
        )
    )["data"]["user"]["events"]

    # Ensure the correct count of events was returned
    assert len(received_customer_events) == len(
        customer_events
    ), "Not all expected customer events were returned"
    assert len(received_staff_events) == len(
        staff_events
    ), "Not all expected staff events were returned"

    # Ensure the events have the expected base customer event data
    for event_node, db_event_object in zip(received_customer_events, customer_events):
        events_checks.assert_is_proper_customer_event_node(event_node, db_event_object)

    # Prepare the events to check them individually
    received_customer_events = iter(received_customer_events)
    received_staff_events = iter(received_staff_events)

    # Test the order placement event
    placed_order_event = next(received_customer_events)
    events_checks.assert_additional_customer_event_node(
        placed_order_event,
        expected_count=None,
        expected_message=None,
        expected_order_line=None,
    )

    # Test the order note added event
    note_added_event = next(received_customer_events)
    events_checks.assert_additional_customer_event_node(
        note_added_event,
        expected_count=None,
        expected_message="418 - I'm a teapot.",
        expected_order_line=None,
    )

    # Test the a digital good was downloaded event
    download_event = next(received_customer_events)
    events_checks.assert_additional_customer_event_node(
        download_event,
        expected_count=None,
        expected_message=None,
        expected_order_line=order_line,
    )

    # Process the staff event: customers were deleted
    customer_deleted_event = next(received_staff_events)
    events_checks.assert_additional_customer_event_node(
        customer_deleted_event,
        expected_count=123,
        expected_message=None,
        expected_order_line=None,
    )

    # Ensure all events were tested
    assert next(received_customer_events, None) is None
    assert next(received_staff_events, None) is None


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
