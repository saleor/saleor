from typing import List, Optional

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


def was_digital_good_download_event_properly_generated(
    download_event: customer_events.CustomerEvent,
    expected_order_line: Optional[customer_events.OrderLine],
    expected_user: Optional[customer_events.UserType],
):
    """Ensure a digital good download event was properly generated
    during a given test case."""

    # Check that the event contains all the expected and valid data
    assert download_event.type == customer_events.CustomerEvents.DIGITAL_LINK_DOWNLOADED
    assert download_event.user == expected_user
    assert download_event.order == expected_order_line.order
    assert download_event.parameters == {"order_line_pk": expected_order_line.pk}
