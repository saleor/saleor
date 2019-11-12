import pytest

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.manager import ExtensionsManager
from saleor.extensions.models import PluginConfiguration
from tests.extensions.sample_plugins import PluginInactive, PluginSample


@pytest.fixture
def plugin_configuration(db):
    plugin = PluginSample()
    configuration, _ = PluginConfiguration.objects.get_or_create(
        name=PluginSample.PLUGIN_NAME, defaults=plugin._get_default_configuration()
    )
    return configuration


@pytest.fixture
def inactive_plugin_configuration(db):
    plugin = PluginInactive()
    return PluginConfiguration.objects.get_or_create(
        name=PluginInactive.PLUGIN_NAME, defaults=plugin._get_default_configuration()
    )[0]


@pytest.fixture
def new_config():
    return {"name": "Foo", "value": "bar"}


@pytest.fixture
def new_config_structure():
    return {"type": ConfigurationTypeField.STRING, "help_text": "foo", "label": "foo"}


@pytest.fixture
def manager_with_plugin_enabled():
    plugins = ["tests.extensions.sample_plugins.PluginSample"]
    manager = ExtensionsManager(plugins=plugins)
    manager.get_plugin_configuration(plugin_name="Plugin Sample")
    return manager


@pytest.fixture
def manager_with_plugin_without_configuration_enabled():
    plugins = ["tests.extensions.sample_plugins.PluginInactive"]
    manager = ExtensionsManager(plugins=plugins)
    manager.get_plugin_configuration(plugin_name="PluginInactive")
    return manager
