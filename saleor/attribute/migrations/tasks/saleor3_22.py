from django.conf import settings
from django.db import connection, transaction
from django.db.models import F, FloatField
from django.db.models.functions import Cast

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import AssignedVariantAttributeValue
from ...models.base import AttributeValue

# Takes around 0.11 seconds to process the batch.
# The memory usage is marginal (~1MB).
BATCH_SIZE = 500


@app.task
@allow_writer()
def fulfill_attribute_value_numeric_field(attribute_value_pk=0):
    value_ids = list(
        AttributeValue.objects.filter(
            pk__gte=attribute_value_pk,
            numeric__isnull=True,
            attribute__input_type="numeric",
        )
        .order_by("pk")
        .values_list("id", flat=True)[:BATCH_SIZE]
    )

    if not value_ids:
        return

    with transaction.atomic():
        locked_values = (
            AttributeValue.objects.filter(id__in=value_ids)
            .order_by("sort_order", "pk")
            .select_for_update()
            .values_list("id", flat=True)
        )
        AttributeValue.objects.filter(id__in=locked_values).update(
            numeric=Cast(F("name"), FloatField())
        )
    fulfill_attribute_value_numeric_field.delay(value_ids[-1])


def update_product_variant_assignment():
    """Assign variant_id to a new field on assignedproductattributevalue.

    Take the values from attribute_assignedvariantattribute to variant_id and copy it over
    to attribute_assignedvariantattributevalue variant_id.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE attribute_assignedvariantattributevalue
            SET variant_id = (
                SELECT variant_id
                FROM attribute_assignedvariantattribute
                WHERE attribute_assignedvariantattributevalue.assignment_id = attribute_assignedvariantattribute.id
            )
            WHERE id IN (
                SELECT ID FROM attribute_assignedvariantattributevalue
                ORDER BY ID DESC
                FOR UPDATE
                LIMIT %s
            );
            """,
            [BATCH_SIZE],
        )


@app.task
@allow_writer()
def assign_product_variants_to_attribute_values_task():
    # Order events proceed from the newest to the oldest
    database_connection_name = settings.DATABASE_CONNECTION_REPLICA_NAME
    assigned_values = (
        AssignedVariantAttributeValue.objects.filter(variant__isnull=True)
        .using(database_connection_name)
        .values_list("pk", flat=True)
        .exists()
    )
    # If we found data, queue next execution of the task
    if assigned_values:
        update_product_variant_assignment()
        assign_product_variants_to_attribute_values_task.delay()
