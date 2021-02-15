import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from ..apps import PluginConfig


@override_settings(PLUGINS_MANAGER=None)
def test_missing_plugin_manager_in_settings():
    with pytest.raises(ImproperlyConfigured):
        PluginConfig.load_and_check_plugins_manager(None)


@override_settings(PLUGINS_MANAGER="")
def test_empty_plugin_manager_in_settings():
    with pytest.raises(ImproperlyConfigured):
        PluginConfig.load_and_check_plugins_manager(None)


@override_settings(PLUGINS_MANAGER="saleor.core.plugins.wrong_path.Manager")
def test_invalid_plugin_manager_in_settings():
    with pytest.raises(ImportError):
        PluginConfig.load_and_check_plugins_manager(None)


def test_empty_plugin_path():
    plugin_path = ""
    with pytest.raises(ImportError):
        PluginConfig.load_and_check_plugin(None, plugin_path)


def test_invalid_plugin_path():
    plugin_path = "saleor.core.plugins.wrong_path.Plugin"
    with pytest.raises(ImportError):
        PluginConfig.load_and_check_plugin(None, plugin_path)
