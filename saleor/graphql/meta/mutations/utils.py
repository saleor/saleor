from django.core.exceptions import ValidationError
from django.db import DatabaseError
from django.db.models import F, JSONField, Value
from django.utils import timezone

from ....checkout.models import Checkout
from ....checkout.utils import get_or_create_checkout_metadata
from ....core.db.expressions import PostgresJsonConcatenate
from ....core.error_codes import MetadataErrorCode
from ....core.models import ModelWithMetadata


def get_valid_metadata_instance(instance) -> ModelWithMetadata:
    if isinstance(instance, Checkout):
        instance = get_or_create_checkout_metadata(instance)
    return instance


TYPE_UPDATED_FIELD = {
    "Checkout": "last_change",
    "Order": "updated_at",
    "Product": "updated_at",
    "ProductVariant": "updated_at",
    "TransactionItem": "modified_at",
    "User": "updated_at",
    "Promotion": "updated_at",
    "Payment": "modified_at",
}


def save_instance(instance, metadata_fields: list):
    updated_field = TYPE_UPDATED_FIELD.get(instance.__class__.__name__)
    if updated_field:
        metadata_fields.append(updated_field)

    try:
        instance.save(update_fields=metadata_fields)
    except DatabaseError as e:
        msg = "Cannot update metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        ) from e


def get_extra_update_field(instance):
    updated_field = TYPE_UPDATED_FIELD.get(instance.__class__.__name__)
    if updated_field:
        return {updated_field: timezone.now()}
    return {}


def update_metadata(instance, items):
    extra_update_fields = get_extra_update_field(instance)

    updated = instance._meta.model.objects.filter(pk=instance.pk).update(
        metadata=PostgresJsonConcatenate(
            F("metadata"), Value(items, output_field=JSONField())
        ),
        **extra_update_fields,
    )
    if not updated:
        msg = "Cannot update metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        )


def update_private_metadata(instance, items):
    extra_update_fields = get_extra_update_field(instance)
    updated = instance._meta.model.objects.filter(pk=instance.pk).update(
        private_metadata=PostgresJsonConcatenate(
            F("private_metadata"), Value(items, output_field=JSONField())
        ),
        **extra_update_fields,
    )
    if not updated:
        msg = (
            "Cannot update private metadata for instance. Updating not existing object."
        )
        raise ValidationError(
            {
                "private_metadata": ValidationError(
                    msg, code=MetadataErrorCode.NOT_FOUND.value
                )
            }
        )
