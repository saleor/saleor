from celery.utils.log import get_task_logger
from django.utils import timezone

from ..celeryconf import app
from .models import Allocation, PreorderReservation, Reservation

task_logger = get_task_logger(__name__)


@app.task
def delete_empty_allocations_task():
    count, _ = Allocation.objects.filter(quantity_allocated=0).delete()
    if count:
        task_logger.debug("Removed %s allocations", count)


@app.task
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
