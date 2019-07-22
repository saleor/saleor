import pytest

from saleor.order.events import OrderEvents
from saleor.order.models import OrderEvent
from saleor.order.utils import change_order_line_quantity


@pytest.mark.parametrize(
    "previous_quantity,new_quantity,added_count,removed_count",
    ((5, 2, 0, 3), (2, 5, 3, 0), (2, 0, 0, 2), (5, 5, 0, 0)),
)
def test_change_quantity_generates_proper_event(
    previous_quantity,
    new_quantity,
    added_count,
    removed_count,
    order_with_lines,
    staff_user,
):

    assert not OrderEvent.objects.exists()

    line = order_with_lines.lines.last()
    line.quantity = previous_quantity

    change_order_line_quantity(staff_user, line, previous_quantity, new_quantity)

    if removed_count:
        expected_type = OrderEvents.DRAFT_REMOVED_PRODUCTS
        expected_quantity = removed_count
    elif added_count:
        expected_type = OrderEvents.DRAFT_ADDED_PRODUCTS
        expected_quantity = added_count
    else:
        # No event should have occurred
        assert not OrderEvent.objects.exists()
        return

    new_event = OrderEvent.objects.last()  # type: OrderEvent
    assert new_event.type == expected_type
    assert new_event.user == staff_user
    assert new_event.parameters == {
        "lines": [
            {"quantity": expected_quantity, "line_pk": line.pk, "item": str(line)}
        ]
    }
