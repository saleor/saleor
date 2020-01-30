import importlib
from typing import List

from .checks import check_extensions  # NOQA: F401


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


class ConfigurationTypeField:
    STRING = "String"
    BOOLEAN = "Boolean"
    SECRET = "Secret"
    PASSWORD = "Password"
    CHOICES = [
        (STRING, "Field is a String"),
        (BOOLEAN, "Field is a Boolean"),
        (SECRET, "Field is a Secret"),
        (PASSWORD, "Field is a Password"),
    ]
