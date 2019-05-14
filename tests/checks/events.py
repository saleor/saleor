from typing import Dict, List, Optional

import graphene

from saleor.account import events as customer_events
from saleor.account.models import User


def _check_customer_deleted_event_is_valid(
    deletion_event: customer_events.CustomerEvent,
    staff_user: User,
    expected_deletion_count=1,
):
    # Ensure the proper event data was set
    assert deletion_event.user == staff_user
    assert deletion_event.type == customer_events.CustomerEvents.CUSTOMER_DELETED
    assert deletion_event.order is None
    assert deletion_event.parameters == {"count": expected_deletion_count}


def was_customer_properly_deleted(staff_user: User, customer_user: User):
    """Ensure the customer was properly deleted
    and any related event was properly triggered"""

    # Ensure the user was properly deleted
    assert not User.objects.filter(pk=customer_user.pk).exists()

    # Ensure the proper event was generated
    deletion_event = customer_events.CustomerEvent.objects.get()

    # Ensure the proper event data was set
    _check_customer_deleted_event_is_valid(deletion_event, staff_user)


def were_customers_properly_deleted(
    staff_user: User, deleted_customers: List[User], saved_customers: List[User]
):
    """Ensure given customers were properly deleted and others properly saved
    and any related event was properly triggered"""

    # Ensure the customers were properly deleted and others were preserved
    assert not User.objects.filter(
        id__in=[user.id for user in deleted_customers]
    ).exists()
    assert User.objects.filter(
        id__in=[user.id for user in saved_customers]
    ).count() == len(saved_customers)

    # Ensure the proper event was generated
    deletion_event = customer_events.CustomerEvent.objects.get()

    # Ensure the proper event data was set for the bulk action
    _check_customer_deleted_event_is_valid(
        deletion_event, staff_user, len(deleted_customers)
    )


def assert_is_proper_customer_event_node(
    received_node: Dict, event: customer_events.CustomerEvent
):
    expected_event_id = graphene.Node.to_global_id("CustomerEvent", event.id)
    expected_user_id = graphene.Node.to_global_id("User", event.user.id)

    assert received_node["id"] == expected_event_id
    assert received_node["date"] == event.date.isoformat()
    assert received_node["type"] == event.type.upper(), f"got {received_node['type']}"
    assert received_node["user"]["id"] == expected_user_id

    if event.order is not None:
        expected_order_id = graphene.Node.to_global_id("Order", event.order.pk)
        assert received_node["order"]["id"] == expected_order_id
    else:
        assert received_node["order"] is None


def assert_additional_customer_event_node(
    received_node: Dict,
    *,
    expected_count: Optional[int],
    expected_message: Optional[str],
    expected_order_line: Optional[customer_events.OrderLine],
):
    """This check is here to ensure every field is checked,
    that no field is *ever* forgotten to be checked."""

    assert received_node["count"] == expected_count
    assert received_node["message"] == expected_message

    received_order_line = received_node["orderLine"]
    if expected_order_line:
        expected_order_line_id = graphene.Node.to_global_id(
            "OrderLine", expected_order_line.id
        )
        assert received_order_line is not None, "expected to receive an order line"
        assert received_order_line["id"] == expected_order_line_id
    else:
        assert received_order_line is None
