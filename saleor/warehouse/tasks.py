from celery.utils.log import get_task_logger

from ..celeryconf import app
from .models import Allocation

task_logger = get_task_logger(__name__)


@app.task
def delete_empty_allocations_task():
    count, _ = Allocation.objects.filter(quantity_allocated=0).delete()
    if count:
        task_logger.debug("Removed %s allocations", count)
