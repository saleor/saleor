from ....celeryconf import app
from ...models import AssignedProductAttributeValue, AssignedPageAttributeValue

from django.db import transaction, connection

# batch size to make sure that task is completed in 1 second
# and we don't use too much memory
BATCH_SIZE = 1000
PAGE_BATCH_SIZE = 5000


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


def update_page_assignment():
    """Update Page assignment.

    Update a batch of 'AssignedPageAttributeValue' rows by setting their 'page' based
    on their related 'assignment'.

    The number of rows updated in each batch is determined by the BATCH_SIZE.
    Rows are locked during the update to prevent concurrent modifications.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH limited AS (
                SELECT av.id
                FROM attribute_assignedpageattributevalue AS av
                WHERE av.page_id IS NULL
                ORDER BY av.id DESC
                LIMIT %s
                FOR UPDATE
            )
            UPDATE attribute_assignedpageattributevalue AS av
            SET page_id = apa.page_id
            FROM attribute_assignedpageattribute AS apa
            WHERE av.id IN (SELECT id FROM limited)
            AND av.assignment_id = apa.id;
            """,  # noqa
                [PAGE_BATCH_SIZE],
            )


@app.task
def assign_pages_to_attribute_values_task():
    """Celery task to update 'AssignedPageAttributeValue' rows in batches.

    Checks for rows where the 'page' is null and updates them based on their
    related 'assignment'. After updating a batch, the task schedules
    itself for the next batch if more rows need updating.
    """
    assigned_values = (
        AssignedPageAttributeValue.objects.filter(page__isnull=True)
        .values_list("pk", flat=True)
        .exists()
    )
    # If we found data, queue next execution of the task
    if assigned_values:
        update_page_assignment()
        assign_pages_to_attribute_values_task.delay()
