from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import DatabaseError

from ....core.error_codes import MetadataErrorCode


def save_instance(instance, metadata_field: str):
    fields = [metadata_field]

    try:
        if bool(instance._meta.get_field("updated_at")):
            fields.append("updated_at")
    except FieldDoesNotExist:
        pass

    try:
        instance.save(update_fields=fields)
    except DatabaseError:
        msg = "Cannot update metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        )
