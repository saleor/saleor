from celery.utils.log import get_task_logger
from django.conf import settings

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ...models import CustomerEvent

# Kills the task if it recurses more than 10000 times (=> 10M rows),
# something is likely wrong if it does. Assuming 1 task = 1sec, it would
# take ~3 hours to abort.
DELETE_DIGITAL_CUSTOMER_EVENTS_MAX_DEPTH = 10000
DELETE_DIGITAL_CUSTOMER_EVENTS_BATCH_SIZE = 1000


task_logger = get_task_logger(f"{__name__}.celery")


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def delete_digital_customer_events(
    current_depth: int, max_depth: int = DELETE_DIGITAL_CUSTOMER_EVENTS_MAX_DEPTH
):
    """Delete any event found in DB for legacy digital orders.

    Support for legacy digital orders has been removed for this Saleor
    version (v3.23.0), thus they need to be dropped from DB in v3.23.0.
    Then, in v3.24.0, the ``CustomerEventsEnum`` will no longer support
    legacy digital orders. This ensures zero downtime (otherwise it would
    crash if any user attempts to fetch customer events before this task
    completes).
    """

    if current_depth > max_depth:
        raise RecursionError(
            f"Data migration for digital order events has recursed "
            f"{current_depth} times. Is the job stuck? Please check the "
            f"database whether there are too many rows to delete "
            f"(see queryset in the Python code for reference). Rerun this task "
            f"manually if there is a lot of data to delete, you can also "
            f"override the ``max_depth`` to allow this task to recurse deeper."
        )

    inner_qs = (
        CustomerEvent.objects.filter(type="digital_link_downloaded")
        .order_by()
        .values_list("id", flat=True)[:DELETE_DIGITAL_CUSTOMER_EVENTS_BATCH_SIZE]
    )

    # WARNING: this does a parallel seq scan of the whole table
    delete_qs = CustomerEvent.objects.filter(pk__in=inner_qs)

    deleted_count = delete_qs._raw_delete(delete_qs.db)
    task_logger.info("Deleted %d order events regarding digital orders", deleted_count)

    # Retrigger the task if there's more to delete
    if deleted_count == DELETE_DIGITAL_CUSTOMER_EVENTS_BATCH_SIZE:
        delete_digital_customer_events.delay(
            current_depth=current_depth + 1, max_depth=max_depth
        )
