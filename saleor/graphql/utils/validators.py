from django.core.exceptions import ValidationError

from ..core.utils import get_duplicates_items


def check_for_duplicates(
    input_data: dict, add_field: str, remove_field: str, error_class_field: str
):
    """Check if any items are on both input field.

    Raise error if some of items are duplicated.
    """
    error = None
    duplicated_items = get_duplicates_items(
        input_data.get(add_field), input_data.get(remove_field)
    )
    if duplicated_items:
        # add error
        error_msg = (
            "The same object cannot be in both list for adding and removing items."
        )
        params = {error_class_field: list(duplicated_items)}
        error = ValidationError(message=error_msg, params=params)

    return error
