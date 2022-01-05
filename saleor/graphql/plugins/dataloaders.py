from collections import defaultdict

from ...plugins.models import EmailTemplate, PluginConfiguration
from ..core.dataloaders import DataLoader


class PluginConfigurationByIdLoader(DataLoader):
    context_key = "plugin_configuration_by_id"

    def batch_load(self, keys):
        plugin_configs = PluginConfiguration.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [plugin_configs.get(plugin_config_id) for plugin_config_id in keys]


class EmailTemplatesByPluginConfigurationLoader(DataLoader):
    """Loads pages by pages type ID."""

    context_key = "email_template_by_plugin_configuration"

    def batch_load(self, keys):
        email_templates = EmailTemplate.objects.using(
            self.database_connection_name
        ).filter(plugin_configuration_id__in=keys)

        config_to_template = defaultdict(list)
        for et in email_templates:
            config_to_template[et.plugin_configuration_id].append(et)

        return [config_to_template[key] for key in keys]
