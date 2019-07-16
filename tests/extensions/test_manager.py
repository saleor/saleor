from saleor.core.extensions.manager import BaseManager, get_extensions_manager
from saleor.core.extensions.plugin import BasePlugin


class TestPlugin(BasePlugin):
    """"""


def test_get_extensions_manager():
    manager_path = "saleor.core.extensions.manager.BaseManager"
    plugin_path = "tests.extensions.test_manager.TestPlugin"
    manager = get_extensions_manager(manager_path=manager_path, plugins=[plugin_path])
    assert isinstance(manager, BaseManager)
    assert len(manager.plugins) == 1
