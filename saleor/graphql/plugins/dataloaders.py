from collections import defaultdict
from functools import partial, wraps

from promise import Promise

from ...plugins.manager import PluginsManager, get_plugins_manager
from ...plugins.models import EmailTemplate
from ..app.dataloaders import get_app_promise
from ..core import SaleorContext
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
        allow_replica = getattr(self.context, "allow_replica", True)
        return [get_plugins_manager(lambda: key, allow_replica) for key in keys]


class AnonymousPluginManagerLoader(DataLoader):
    context_key = "anonymous_plugin_manager"

    def batch_load(self, keys):
        allow_replica = getattr(self.context, "allow_replica", True)
        return [get_plugins_manager(None, allow_replica) for key in keys]


def plugin_manager_promise(context: SaleorContext, app) -> Promise[PluginsManager]:
    user = context.user
    requestor = app or user
    if requestor is None:
        return AnonymousPluginManagerLoader(context).load("Anonymous")
    return PluginManagerByRequestorDataloader(context).load(requestor)


def get_plugin_manager_promise(context: SaleorContext) -> Promise[PluginsManager]:
    return get_app_promise(context).then(
        partial(plugin_manager_promise, context)  # type: ignore[arg-type] # mypy incorrectly assumes the return type to be a promise of a promise # noqa: E501
    )


def plugin_manager_promise_callback(func):
    @wraps(func)
    def _wrapper(root, info, *args, **kwargs):
        return get_plugin_manager_promise(info.context).then(
            partial(func, root, info, *args, **kwargs)
        )

    return _wrapper
