from django.core.exceptions import ValidationError

from ..core.utils import get_duplicates_ids


def check_for_duplicates(
    input_data: dict, add_field: str, remove_field: str, error_class_field: str
):
    """Check if any items are on both input field.

    Raise error if some of items are duplicated.
    """
    error = None
    duplicated_ids = get_duplicates_ids(
        input_data.get(add_field), input_data.get(remove_field)
    )
    if duplicated_ids:
        # add error
        error_msg = (
            "The same object cannot be in both list" "for adding and removing items."
        )
        params = {error_class_field: list(duplicated_ids)}
        error = ValidationError(message=error_msg, params=params)

    return error
