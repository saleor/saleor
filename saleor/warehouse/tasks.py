from celery.utils.log import get_task_logger
from django.db.models import Sum
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
    count = 0
    corrected_count = 0
    for stock in Stock.objects.iterator():
        count += 1
        quantity_allocated = stock.allocations.aggregate(
            quantity_allocated=Coalesce(Sum("quantity_allocated"), 0)
        )["quantity_allocated"]
        if stock.quantity_allocated != quantity_allocated:
            task_logger.info(
                "Mismatch updating quantity_allocated: stock {} had "
                "{} allocated, but should have {}.".format(
                    stock.pk, stock.quantity_allocated, quantity_allocated
                )
            )
            stock.quantity_allocated = quantity_allocated
            stock.save(update_fields=["quantity_allocated"])
            corrected_count += 1
    task_logger.info(
        "Finished updating quantity_allocated on stocks, from {}, "
        "{} were corrected.".format(count, corrected_count)
    )
