from unittest.mock import patch

import pytest

from saleor.events.models import OrderEvent
from saleor.events.order import OrderEventManager


@patch.object(OrderEvent, 'save')
@patch.object(OrderEvent.objects, 'bulk_create')
@pytest.mark.parametrize('event_count', (0, 1, 2, 5))
def test_manager_event_creation(mocked_bulk, mocked_save, event_count):
    # create the event current scope's manager
    manager = OrderEventManager()
    assert manager.base_type is OrderEvent

    for current_count in range(1, event_count + 1):
        # Ensure the manager returns the same instance object
        # as the current manager
        assert manager.new_event().instances is manager.instances

        # Ensure the manager correctly added the new instance
        assert len(manager.instances) == current_count

    # commit the events
    manager.save()

    # single instance or none
    if event_count < 1:
        assert mocked_bulk.call_count == 0

    # bulk creation
    if event_count > 1:
        assert mocked_bulk.call_count == 1

    # no instance
    if event_count == 0:
        assert mocked_save.call_count == 0

    # single instance
    if event_count == 1:
        assert mocked_save.call_count == 1


def test_manager_has_no_side_effects():
    first_manager = OrderEventManager()
    second_manager = OrderEventManager()
    assert first_manager.instances is not second_manager.instances
