from ..utils import is_event_active_for_any_plugin


class MockInvoicePluginActive:
    active = True

    @staticmethod
    def is_event_active(_):
        return True


class MockInvoicePluginInactive:
    active = False

    @staticmethod
    def is_event_active(_):
        return True


def test_is_event_active_for_any_plugin_plugin_active():
    result = is_event_active_for_any_plugin(
        "event", [MockInvoicePluginActive(), MockInvoicePluginInactive()]
    )
    assert result is True


def test_is_event_active_for_any_plugin_plugin_inactive():
    result = is_event_active_for_any_plugin(
        "event", [MockInvoicePluginInactive(), MockInvoicePluginInactive()]
    )
    assert result is False
