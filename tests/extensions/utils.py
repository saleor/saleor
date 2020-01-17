from typing import Dict, List, Union


def get_config_value(
    field_name: str, configuration: List[Dict[str, Union[str, bool]]]
) -> Union[str, bool, None]:
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]
    return None
