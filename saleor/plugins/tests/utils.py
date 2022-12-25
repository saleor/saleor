def get_config_value(
    field_name: str, configuration: list[dict[str, str | bool]]
) -> str | bool | None:
    for elem in configuration:
        if elem["name"] == field_name:
            return elem["value"]
    return None
