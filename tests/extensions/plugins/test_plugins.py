import copy

from saleor.extensions import ConfigurationTypeField
from saleor.extensions.models import PluginConfiguration
from tests.extensions.sample_plugins import PluginSample
from tests.extensions.utils import get_config_value


def test_update_config_items_keeps_bool_value(plugin_configuration):
    data_to_update = [
        {"name": "Username", "value": "new_admin@example.com"},
        {"name": "Use sandbox", "value": False},
    ]
    plugin_sample = PluginSample()
    qs = PluginConfiguration.objects.all()
    configuration = PluginSample.get_plugin_configuration(qs)
    plugin_sample._update_config_items(data_to_update, configuration.configuration)
    configuration.save()
    configuration.refresh_from_db()
    assert get_config_value("Use sandbox", configuration.configuration) is False


def test_update_config_items_convert_to_bool_value():
    data_to_update = [
        {"name": "Username", "value": "new_admin@example.com"},
        {"name": "Use sandbox", "value": "false"},
    ]
    plugin_sample = PluginSample()
    plugin_sample._initialize_plugin_configuration()
    qs = PluginConfiguration.objects.all()
    configuration = PluginSample.get_plugin_configuration(qs)
    plugin_sample._update_config_items(data_to_update, configuration.configuration)
    configuration.save()
    configuration.refresh_from_db()
    assert get_config_value("Use sandbox", configuration.configuration) is False


def test_base_plugin__update_configuration_structure_configuration_has_not_change(
    plugin_configuration
):
    plugin = PluginSample()
    old_configuration = plugin_configuration.configuration.copy()
    plugin._update_configuration_structure(plugin_configuration)
    plugin_configuration.refresh_from_db()
    assert old_configuration == plugin_configuration.configuration


def test_base_plugin__update_configuration_structure_configuration_has_change(
    monkeypatch, plugin_configuration
):
    old_configuration = plugin_configuration.configuration.copy()
    plugin = PluginSample()
    config_structure = plugin.CONFIG_STRUCTURE
    config_structure["Private key"] = {
        "help_text": "Test",
        "label": "Test",
        "type": ConfigurationTypeField.STRING,
    }
    default_configuration = plugin._get_default_configuration()
    private_key_dict = {"name": "Private key", "value": "123457"}
    default_configuration["configuration"].append(private_key_dict)
    monkeypatch.setattr(
        "tests.extensions.plugins.test_plugins.PluginSample._get_default_configuration",
        lambda: default_configuration,
    )
    plugin._update_configuration_structure(plugin_configuration)
    plugin_configuration.refresh_from_db()
    assert len(old_configuration) + 1 == len(plugin_configuration.configuration)
    old_configuration.append(private_key_dict)
    assert old_configuration == plugin_configuration.configuration


def test_base_plugin__append_config_structure_do_not_save_to_db(plugin_configuration):
    plugin = PluginSample()
    old_config = copy.deepcopy(plugin_configuration.configuration)
    plugin._append_config_structure(plugin_configuration.configuration)
    for elem in old_config:
        for new_elem in plugin_configuration.configuration:
            if elem["name"] == new_elem["name"]:
                assert not elem == new_elem
    plugin_configuration.refresh_from_db()
    assert old_config == plugin_configuration.configuration
    for elem in plugin_configuration.configuration:
        assert set(elem.keys()) == {"name", "value"}
