from unittest.mock import patch

from saleor.core.extensions.dummy_plugin import DummyPlugin
from saleor.core.extensions.manager import BaseManager, get_extensions_manager


def test_get_extensions_manager():
    manager_path = "saleor.core.extensions.manager.BaseManager"
    dummy_plugin_path = "saleor.core.extensions.dummy_plugin.DummyPlugin"
    manager = get_extensions_manager(
        manager_path=manager_path, plugins=[dummy_plugin_path]
    )
    assert isinstance(manager, BaseManager)
    assert len(manager.plugins) == 1
    assert isinstance(manager.plugins[0], DummyPlugin)


@patch.object(DummyPlugin, "calculate_checkout_total")
def test_manager_can_run_plugin_methods(
    mock_calculate, checkout_with_item, discount_info
):
    dummy_plugin_path = "saleor.core.extensions.dummy_plugin.DummyPlugin"
    manager = BaseManager(plugins=[dummy_plugin_path])
    discounts = [discount_info]
    manager.calculate_checkout_total(checkout_with_item, discounts)
    assert mock_calculate.called
