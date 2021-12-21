from celery.utils.log import get_task_logger

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
    for stock in Stock.objects.iterator():
        stock.recalculate_quantity_allocated()
    task_logger.debug("Updated quantity_allocated on all stocks.")
