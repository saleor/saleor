import pytest

from ..events import call_event


def test_call_event_cannot_be_used_with_checkout_info_object(
    checkout_info, plugins_manager
):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout_info)


def test_call_event_cannot_be_used_with_checkout_object(checkout, plugins_manager):
    with pytest.raises(NotImplementedError):
        call_event(plugins_manager.checkout_updated, checkout)
