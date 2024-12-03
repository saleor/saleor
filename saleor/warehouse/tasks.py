from celery.utils.log import get_task_logger
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from ..celeryconf import app
from ..core.db.connection import allow_writer
from .management import delete_allocations, stock_bulk_update
from .models import Allocation, PreorderReservation, Reservation, Stock

task_logger = get_task_logger(__name__)


@app.task
@allow_writer()
def delete_empty_allocations_task():
    ids_to_delete = list(
        Allocation.objects.filter(quantity_allocated=0).values_list("id", flat=True)
    )
    count, _ = delete_allocations(ids_to_delete)
    if count:
        task_logger.debug("Removed %s allocations", count)


@app.task
@allow_writer()
def delete_expired_reservations_task():
    stock_reservations, _ = Reservation.objects.filter(
        reserved_until__lt=timezone.now()
    ).delete()
    preorder_reservations, _ = PreorderReservation.objects.filter(
        reserved_until__lt=timezone.now()
    ).delete()

    if stock_reservations or preorder_reservations:
        task_logger.debug(
            "Removed %s stock reservations and %s preorder reservations",
            stock_reservations,
            preorder_reservations,
        )


@app.task
@allow_writer()
def update_stocks_quantity_allocated_task():
    stocks_to_update = []
    for mismatched_stock in Stock.objects.annotate(
        allocations_allocated=Coalesce(Sum("allocations__quantity_allocated"), 0)
    ).exclude(quantity_allocated=F("allocations_allocated")):
        allocations_allocated = getattr(
            mismatched_stock, "allocations_allocated"
        )  # annotation
        task_logger.info(
            "Mismatch updating quantity_allocated: stock %d had "
            "%d allocated, but should have %d.",
            mismatched_stock.pk,
            mismatched_stock.quantity_allocated,
            allocations_allocated,
        )
        mismatched_stock.quantity_allocated = allocations_allocated
        stocks_to_update.append(mismatched_stock)

    stock_bulk_update(stocks_to_update, ["quantity_allocated"])

    task_logger.info(
        "Finished updating quantity_allocated on stocks, %d were corrected.",
        len(stocks_to_update),
    )
