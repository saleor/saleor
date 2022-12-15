from collections import defaultdict
from functools import partial, wraps

from ...plugins.manager import get_plugins_manager
from ...plugins.models import EmailTemplate
from ..app.dataloaders import get_app_promise
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
    context_key = "plugin_manager_by_requestor"

    def batch_load(self, keys):
        return [get_plugins_manager(lambda: key) for key in keys]


class AnonymousPluginManagerLoader(DataLoader):
    context_key = "anonymous_plugin_manager"

    def batch_load(self, keys):
        return [get_plugins_manager() for key in keys]


def plugin_manager_promise(request, app):
    user = request.user
    requestor = app or user
    if requestor is None:
        return AnonymousPluginManagerLoader(request).load("Anonymous")
    return PluginManagerByRequestorDataloader(request).load(requestor)


def get_plugin_manager_promise(request):
    return get_app_promise(request).then(partial(plugin_manager_promise, request))


def plugin_manager_promise_callback(func):
    @wraps(func)
    def _wrapper(root, info, *args, **kwargs):
        return get_plugin_manager_promise(info.context).then(
            partial(func, root, info, *args, **kwargs)
        )

    return _wrapper
