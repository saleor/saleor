from celery.utils.log import get_task_logger
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from ..celeryconf import app
from .models import Allocation, Stock

task_logger = get_task_logger(__name__)


@app.task
def delete_empty_allocations_task():
    count, _ = Allocation.objects.filter(quantity_allocated=0).delete()
    if count:
        task_logger.debug("Removed %s allocations", count)


@app.task
def update_stocks_quantity_allocated_task():
    stocks_to_udpate = []
    for mismatched_stock in Stock.objects.annotate(
        allocations_allocated=Coalesce(Sum("allocations__quantity_allocated"), 0)
    ).exclude(quantity_allocated=F("allocations_allocated")):
        task_logger.info(
            "Mismatch updating quantity_allocated: stock %d had "
            "%d allocated, but should have %d.",
            mismatched_stock.pk,
            mismatched_stock.quantity_allocated,
            mismatched_stock.allocations_allocated,
        )
        mismatched_stock.quantity_allocated = mismatched_stock.allocations_allocated
        stocks_to_udpate.append(mismatched_stock)

    Stock.objects.bulk_update(stocks_to_udpate, ["quantity_allocated"])
    task_logger.info(
        "Finished updating quantity_allocated on stocks, %d were corrected.",
        len(stocks_to_udpate),
    )
