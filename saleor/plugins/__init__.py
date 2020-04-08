import importlib
from typing import List

from .checks import check_plugins  # NOQA: F401

from .base_plugin import BasePlugin, ConfigurationTypeField
from .anonymize.plugin import AnonymizePlugin
from .avatax.plugin import AvataxPlugin
from .vatlayer.plugin import VatlayerPlugin
from .webhook.plugin import WebhookPlugin


def discover_plugins_modules(plugins: List[str]):
    plugins_modules = []
    for dotted_path in plugins:
        try:
            module_path, class_name = dotted_path.rsplit(".", 1)
        except ValueError as err:
            raise ImportError(
                "%s doesn't look like a module path" % dotted_path
            ) from err

        module = importlib.import_module(module_path)
        plugins_modules.append(module.__package__)
    return plugins_modules
