from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from saleor.extensions import ConfigurationType


def get_config_value(
    field_name: str, configuration: "ConfigurationType"
) -> Union[str, bool]:
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]
