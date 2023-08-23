from ....celeryconf import app
from ...models import AssignedProductAttributeValue

from django.db import connection

# batch size to make sure that task is completed in 1 second
# and we don't use too much memory
BATCH_SIZE = 1000


def update_product_assignment():
    """Assign product_id to a new field on assignedproductattributevalue.

    Take the values from attribute_assignedproductattribute to product_id.
    The old field has already been deleted in Django State operations so we need
    to use raw SQL to get the value and copy the assignment from the old table.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE attribute_assignedproductattributevalue
            SET product_id = (
                SELECT product_id
                FROM attribute_assignedproductattribute
                WHERE attribute_assignedproductattributevalue.assignment_id = attribute_assignedproductattribute.id
            )
            WHERE id IN (
                SELECT ID FROM attribute_assignedproductattributevalue
                ORDER BY ID DESC
                FOR UPDATE
                LIMIT %s
            );
            """,  # noqa
            [BATCH_SIZE],
        )


@app.task
def assign_products_to_attribute_values_task():
    # Order events proceed from the newest to the oldest
    assigned_values = (
        AssignedProductAttributeValue.objects.filter(product__isnull=True)
        .values_list("pk", flat=True)
        .exists()
    )
    # If we found data, queue next execution of the task
    if assigned_values:
        update_product_assignment()
        assign_products_to_attribute_values_task.delay()
