from typing import TYPE_CHECKING, List

from django.conf import settings
from django.core.checks import Error, register
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from .base_plugin import BasePlugin


@register()
def check_plugins(app_configs, **kwargs):
    """Confirm a correct import of plugins and manager."""
    errors = []
    check_manager(errors)

    plugins = settings.PLUGINS or []

    for plugin_path in plugins:
        check_single_plugin(plugin_path, errors)

    return errors


def check_manager(errors: List[Error]):
    if not hasattr(settings, "PLUGINS_MANAGER") or not settings.PLUGINS_MANAGER:
        errors.append(Error("Settings should contain PLUGINS_MANAGER env"))
        return

    try:
        import_string(settings.PLUGINS_MANAGER)
    except ImportError:
        errors.append(
            Error("Plugins Manager path: %s doesn't exist" % settings.PLUGINS_MANAGER)
        )


def check_single_plugin(plugin_path: str, errors: List[Error]):
    if not plugin_path:
        errors.append(Error("Wrong plugin_path %s" % plugin_path))
        return
    try:
        plugin_class = import_string(plugin_path)
    except ImportError:
        errors.append(Error("Plugin with path: %s doesn't exist" % plugin_path))

    if not errors:
        check_plugin_fields(["PLUGIN_ID"], plugin_class, errors)


def check_plugin_fields(
    fields: List[str], plugin_class: "BasePlugin", errors: List[Error]
):
    name = plugin_class.__name__  # type: ignore

    for field in fields:
        if not getattr(plugin_class, field, None):
            errors.append(Error(f"Missing field {field} for plugin - {name}"))
