import warnings

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db.models import F, Func, JSONField, TextField, Value
from django.utils import timezone

from ....checkout.models import Checkout, CheckoutMetadata
from ....checkout.utils import get_or_create_checkout_metadata
from ....core.db.connection import allow_writer
from ....core.db.expressions import PostgresJsonConcatenate
from ....core.error_codes import MetadataErrorCode
from ....core.models import ModelWithMetadata


def get_valid_metadata_instance(instance) -> ModelWithMetadata:
    if isinstance(instance, Checkout):
        instance = get_or_create_checkout_metadata(instance)
    return instance


# Mapping of types to their respective field responsible for tracking updates
# In case there is no such field, set value as None
TYPE_UPDATED_FIELD = {
    "Address": None,
    "User": "updated_at",
    "App": None,
    "Attribute": None,
    "Channel": None,
    "Checkout": "last_change",
    "CheckoutLine": None,
    "Voucher": None,
    "Promotion": "updated_at",
    "GiftCard": None,
    "Invoice": None,
    "Menu": None,
    "MenuItem": None,
    "Order": "updated_at",
    "OrderLine": None,
    "Fulfillment": None,
    "Page": None,
    "PageType": None,
    "TransactionItem": "modified_at",
    "Payment": "modified_at",
    "Category": "updated_at",
    "Product": "updated_at",
    "ProductType": None,
    "ProductMedia": None,
    "ProductVariant": "updated_at",
    "DigitalContent": None,
    "Collection": None,
    "ShippingMethod": None,
    "ShippingZone": None,
    "SiteSettings": None,
    "TaxClass": None,
    "TaxConfiguration": None,
    "Warehouse": None,
}


def get_updated_field_name(instance) -> str | None:
    # checkout update are handled in BaseMetaMutations
    if isinstance(instance, CheckoutMetadata):
        return None
    if instance.__class__.__name__ not in TYPE_UPDATED_FIELD:
        warnings.warn(
            f"Updated field for type {instance.__class__.__name__} is not defined in TYPE_UPDATED_FIELD. "
            "Please add an entry to the dictionary.",
            UserWarning,
            stacklevel=2,
        )
    return TYPE_UPDATED_FIELD.get(instance.__class__.__name__)


def get_extra_update_field(instance):
    updated_field = get_updated_field_name(instance)
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
    instance.refresh_from_db(fields=["metadata"])


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
    instance.refresh_from_db(fields=["private_metadata"])


def delete_metadata_keys(instance, keys: list[str]):
    """Atomically delete metadata keys at the database level.

    Performs an atomic operation to remove the specified keys from the
    metadata JSONB field, preventing race conditions that could occur
    with read-modify-write patterns.
    """
    extra_update_fields = get_extra_update_field(instance)

    with allow_writer():
        updated = instance._meta.model.objects.filter(pk=instance.pk).update(
            metadata=Func(
                F("metadata"),
                Value(keys, output_field=ArrayField(TextField())),
                function="-",
                template="%(expressions)s",
                arg_joiner=" - ",
            ),
            **extra_update_fields,
        )
    if not updated:
        msg = "Cannot delete metadata for instance. Updating not existing object."
        raise ValidationError(
            {"metadata": ValidationError(msg, code=MetadataErrorCode.NOT_FOUND.value)}
        )
    instance.refresh_from_db(fields=["metadata"])


def delete_private_metadata_keys(instance, keys: list[str]):
    """Atomically delete private metadata keys at the database level.

    Performs an atomic operation to remove the specified keys from the
    metadata JSONB field, preventing race conditions that could occur
    with read-modify-write patterns.
    """
    extra_update_fields = get_extra_update_field(instance)

    with allow_writer():
        updated = instance._meta.model.objects.filter(pk=instance.pk).update(
            private_metadata=Func(
                F("private_metadata"),
                Value(keys, output_field=ArrayField(TextField())),
                function="-",
                template="%(expressions)s",
                arg_joiner=" - ",
            ),
            **extra_update_fields,
        )
    if not updated:
        msg = (
            "Cannot delete private metadata for instance. Updating not existing object."
        )
        raise ValidationError(
            {
                "private_metadata": ValidationError(
                    msg, code=MetadataErrorCode.NOT_FOUND.value
                )
            }
        )
    instance.refresh_from_db(fields=["private_metadata"])
