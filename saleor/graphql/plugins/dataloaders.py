from collections import defaultdict

from ...plugins.manager import get_plugins_manager
from ...plugins.models import EmailTemplate
from ..app.dataloaders import load_app
from ..core.dataloaders import DataLoader


class EmailTemplatesByPluginConfigurationLoader(DataLoader):
    """Loads email templates by plugin configuration ID."""

    context_key = "email_template_by_plugin_configuration"

    def batch_load(self, keys):
        email_templates = EmailTemplate.objects.using(
            self.database_connection_name
        ).filter(plugin_configuration_id__in=keys)

        config_to_template = defaultdict(list)
        for et in email_templates:
            config_to_template[et.plugin_configuration_id].append(et)

        return [config_to_template[key] for key in keys]


class PluginManagerByRequestorDataloader(DataLoader):
    context_key = "plugin_by_requestor"

    def batch_load(self, keys):
        return [get_plugins_manager(lambda: key) for key in keys]


def load_plugins(request):
    app = load_app(request)
    user = request.user
    requestor = app or user
    return PluginManagerByRequestorDataloader(request).load(requestor).get()
