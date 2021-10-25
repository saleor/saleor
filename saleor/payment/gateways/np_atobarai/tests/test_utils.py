import pytest

from .....order import OrderEvents
from .. import get_payment_name, notify_dashboard


def test_notify_dashboard(order):
    # given
    message = "message"

    # when
    notify_dashboard(order, message)

    # then
    event = order.events.first()
    assert event.type == OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    assert event.parameters["message"] == message


@pytest.mark.parametrize(
    "payment_id, result",
    [
        ("123", "payment with psp reference 123"),
        (123, "payment with id 123"),
        ("", "payment"),
    ],
)
def test_get_payment_name(payment_id, result):
    # when
    payment_name = get_payment_name(payment_id)

    # then
    assert payment_name == result
