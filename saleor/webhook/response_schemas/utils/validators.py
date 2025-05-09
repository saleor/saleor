def lower_values(
    values: str | list[str] | None,
) -> str | list[str] | None:
    """Lowercase all values in a string or a list."""
    match values:
        case str():
            return values.lower()
        case list():
            return [value.lower() for value in values]
        case _:
            return values
