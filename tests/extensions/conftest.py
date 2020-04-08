import pytest

from saleor.plugins import ConfigurationTypeField
from saleor.plugins.models import PluginConfiguration
from tests.pliugins.sample_plugins import PluginInactive, PluginSample


@pytest.fixture
def plugin_configuration(db):
    configuration, _ = PluginConfiguration.objects.get_or_create(
        name=PluginSample.PLUGIN_NAME,
        defaults={
            "active": PluginSample.DEFAULT_ACTIVE,
            "configuration": PluginSample.DEFAULT_CONFIGURATION,
            "name": PluginSample.PLUGIN_NAME,
        },
    )
    return configuration


@pytest.fixture
def inactive_plugin_configuration(db):
    return PluginConfiguration.objects.get_or_create(
        name=PluginInactive.PLUGIN_NAME,
        defaults={
            "active": PluginInactive.DEFAULT_ACTIVE,
            "configuration": PluginInactive.DEFAULT_CONFIGURATION,
            "name": PluginInactive.PLUGIN_NAME,
        },
    )[0]


@pytest.fixture
def new_config():
    return {"name": "Foo", "value": "bar"}


@pytest.fixture
def new_config_structure():
    return {"type": ConfigurationTypeField.STRING, "help_text": "foo", "label": "foo"}
