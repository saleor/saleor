from typing import Dict, Union


def get_config_value(
    field_name: str, configuration: Dict[str, Union[str, bool]]
) -> Union[str, bool]:
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]
