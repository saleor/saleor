from django.conf import settings
from django.db import connection

from ....celeryconf import app
from ...models import AssignedVariantAttributeValue

# batch size to make sure that task is completed in 1 second
# and we don't use too much memory
BATCH_SIZE = 1000


def update_product_variant_assignment():
    """Assign product_id to a new field on assignedproductattributevalue.

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
