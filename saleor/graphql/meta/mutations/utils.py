from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import DatabaseError

from ....checkout.models import Checkout
from ....checkout.utils import get_or_create_checkout_metadata
from ....core.error_codes import MetadataErrorCode
from ....core.models import ModelWithMetadata


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
    except DatabaseError as e:
        msg = "Cannot update metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        ) from e
