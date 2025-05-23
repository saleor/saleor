from pydantic import ValidationError


def parse_validation_error(error: ValidationError) -> str:
    """Parse pydantic ValidationError to a human-readable message."""
    errors = error.errors()
    error_msg: list[str] = []
    for error_data in errors:
        field = ""
        loc_data = error_data["loc"]
        if loc_data:
            field = str(loc_data[0])
        if error_data.get("type") == "missing":
            error_msg.append(
                f"Missing value for field: {field}. Input: {error_data['input']}."
            )
        else:
            error_msg.append(
                f"Incorrect value ({error_data['input']}) for field: {field}. Error: {error_data['msg']}."
            )
    return "\n\n".join(error_msg)
