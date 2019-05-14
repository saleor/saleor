from dataclasses import dataclass
from typing import Optional

import graphene
import pytest
from django.db import models

from saleor.account import events as account_events

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


@dataclass
class _ExpectedCustomerEventData:
    id: str
    user: str
    count: Optional[int]
    message: Optional[str]
    order: Optional[str]
    orderLine: Optional[str]  # noqa
    type: str

    def __setattr__(self, key, value):
        """Converts a model object value to a gql node id"""
        if isinstance(value, models.Model):
            value = graphene.Node.to_global_id(value.__class__.__name__, value.pk)
        elif isinstance(value, dict) and len(value) == 1:
            _, value = value.popitem()
        return super().__setattr__(key, value)


@pytest.mark.parametrize(
    "_test_name, event, expected_event_data",
    [
        (
            "customer_placed_order_event",
            lambda **kwargs: account_events.customer_placed_order_event(
                user=kwargs["customer_user"], order=kwargs["order"]
            ),
            lambda **kwargs: _ExpectedCustomerEventData(
                id=kwargs["event"],
                user=kwargs["customer_user"],
                count=None,
                message=None,
                order=kwargs["order"],
                orderLine=None,
                type=account_events.CustomerEvents.PLACED_ORDER.upper(),
            ),
        ),
        (
            "customer_added_to_note_order_event",
            lambda **kwargs: account_events.customer_added_to_note_order_event(
                user=kwargs["customer_user"],
                order=kwargs["order"],
                message="418 - I'm a teapot.",
            ),
            lambda **kwargs: _ExpectedCustomerEventData(
                id=kwargs["event"],
                user=kwargs["customer_user"],
                count=None,
                message="418 - I'm a teapot.",
                order=kwargs["order"],
                orderLine=None,
                type=account_events.CustomerEvents.NOTE_ADDED_TO_ORDER.upper(),
            ),
        ),
        (
            "customer_downloaded_a_digital_link_event",
            lambda **kwargs: account_events.customer_downloaded_a_digital_link_event(
                user=kwargs["customer_user"], order_line=kwargs["order_line"]
            ),
            lambda **kwargs: _ExpectedCustomerEventData(
                id=kwargs["event"],
                user=kwargs["customer_user"],
                count=None,
                message=None,
                order=kwargs["order"],
                orderLine=kwargs["order_line"],
                type=account_events.CustomerEvents.DIGITAL_LINK_DOWNLOADED.upper(),
            ),
        ),
        (
            "staff_user_deleted_a_customer_event",
            lambda **kwargs: account_events.staff_user_deleted_a_customer_event(
                staff_user=kwargs["staff_user"], deleted_count=123
            ),
            lambda **kwargs: _ExpectedCustomerEventData(
                id=kwargs["event"],
                user=kwargs["staff_user"],
                count=123,
                message=None,
                order=None,
                orderLine=None,
                type=account_events.CustomerEvents.CUSTOMER_DELETED.upper(),
            ),
        ),
    ],
)
def test_account_events_resolve_properly(
    staff_api_client,
    staff_user,
    customer_user,
    order_line,
    permission_manage_users,
    _test_name,
    event,
    expected_event_data,
):
    """Create every possible event and attempt to resolve them and
    check if they properly returned all the expected data."""

    # Prepare test
    order = order_line.order
    staff_api_client.user.user_permissions.add(permission_manage_users)
    event = event(**locals())  # type: account_events.CustomerEvent
    expected_event_data = expected_event_data(
        **locals()
    )  # type: _ExpectedCustomerEventData

    # Retrieve the events
    event_associated_user = event.user

    received_events = get_graphql_content(
        staff_api_client.post_graphql(
            QUERY_CUSTOMER_EVENTS,
            variables={
                "customerId": graphene.Node.to_global_id(
                    "User", event_associated_user.id
                )
            },
        )
    )["data"]["user"]["events"]

    # Ensure the correct count of events was returned
    assert len(received_events) == 1, "The expected event was not returned"
    assert _ExpectedCustomerEventData(**received_events[0]) == expected_event_data


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
