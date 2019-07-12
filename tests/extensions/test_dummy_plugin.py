from saleor.core.extensions.dummy_plugin import DummyPlugin
from saleor.core.extensions.plugin import BasePlugin


def test_dummy_plugin_overwrites_all_base_plugin_methods():
    assert isinstance(BasePlugin(), DummyPlugin.__bases__[0])
    dummy_vars = vars(DummyPlugin)
    for name in vars(BasePlugin):
        if name.startswith("__"):
            continue
        assert name in dummy_vars
