from saleor.extensions.models import PluginConfiguration
from tests.extensions.helpers import PluginSample, get_config_value


def test_update_config_items_keeps_bool_value():
    data_to_update = [
        {"name": "Username", "value": "new_admin@example.com"},
        {"name": "Use sandbox", "value": False},
    ]
    plugin_sample = PluginSample()
    plugin_sample._initialize_plugin_configuration()
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
