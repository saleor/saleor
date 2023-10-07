from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import DatabaseError

from ....checkout.models import Checkout
from ....checkout.utils import get_or_create_checkout_metadata
from ....core.error_codes import MetadataErrorCode
from ....core.models import ModelWithMetadata


# `instance = get_checkout_metadata(instance)` is calling the
# `get_checkout_metadata` function to retrieve the metadata associated with a
# checkout instance. This function is defined in the `.../checkout/utils.py` file
# and takes a `Checkout` instance as an argument. It returns a dictionary
# containing the metadata associated with the checkout.
def get_valid_metadata_instance(instance) -> ModelWithMetadata:
    if isinstance(instance, Checkout):
        instance = get_or_create_checkout_metadata(instance)
    return instance


def save_instance(instance, metadata_fields: list):
    try:
        if bool(instance._meta.get_field("updated_at")):
            metadata_fields.append("updated_at")
    except FieldDoesNotExist:
        pass

    try:
        instance.save(update_fields=metadata_fields)
    except DatabaseError:
        msg = "Cannot update metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        )
