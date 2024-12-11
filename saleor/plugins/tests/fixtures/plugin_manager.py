import pytest

from ...manager import PluginsManager
from ..sample_plugins import ALL_PLUGINS


@pytest.fixture
def plugins_manager():
    return PluginsManager(plugins=[])


@pytest.fixture
def all_plugins_manager():
    plugins_as_module_paths = [p.__module__ + "." + p.__name__ for p in ALL_PLUGINS]
    return PluginsManager(plugins=plugins_as_module_paths)
