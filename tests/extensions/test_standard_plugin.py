from saleor.core.extensions.default_plugin import DefaultPlugin
from saleor.core.extensions.plugin import BasePlugin


def test_standard_plugin_overwrites_all_base_plugin_methods():
    assert isinstance(BasePlugin(), DefaultPlugin.__bases__[0])
    dummy_vars = vars(DefaultPlugin)
    for name in vars(BasePlugin):
        if name.startswith("__"):
            continue
        assert name in dummy_vars
