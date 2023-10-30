from typing import Optional, Union

import celery
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from django.utils import timezone

from ..celeryconf import app
from ..core import JobStatus
from . import events
from .models import ExportEvent, ExportFile
from .notifications import send_export_failed_info
from .utils.export import export_gift_cards, export_products, export_voucher_codes

task_logger = get_task_logger(__name__)


class ExportTask(celery.Task):
    # should be updated when new export task is added
    TASK_NAME_TO_DATA_TYPE_MAPPING = {
        "export-products": "products",
        "export-gift-cards": "gift cards",
        "export-voucher-codes": "voucher codes",
    }

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        export_file_id = args[0]
        export_file = ExportFile.objects.get(pk=export_file_id)

        export_file.content_file = None
        export_file.status = JobStatus.FAILED
        export_file.save(update_fields=["status", "updated_at", "content_file"])

        events.export_failed_event(
            export_file=export_file,
            user=export_file.user,
            app=export_file.app,
            message=str(exc),
            error_type=str(einfo.type),
        )

        data_type = ExportTask.TASK_NAME_TO_DATA_TYPE_MAPPING.get(self.name)
        if not data_type:
            data_type = "unknown data"
        send_export_failed_info(export_file, data_type)

    def on_success(self, retval, task_id, args, kwargs):
        export_file_id = args[0]

        export_file = ExportFile.objects.get(pk=export_file_id)
        export_file.status = JobStatus.SUCCESS
        export_file.save(update_fields=["status", "updated_at"])
        events.export_success_event(
            export_file=export_file, user=export_file.user, app=export_file.app
        )


@app.task(name="export-products", base=ExportTask)
def export_products_task(
    export_file_id: int,
    scope: dict[str, Union[str, dict]],
    export_info: dict[str, list],
    file_type: str,
    delimiter: str = ",",
):
    export_file = ExportFile.objects.get(pk=export_file_id)
    export_products(export_file, scope, export_info, file_type, delimiter)


@app.task(name="export-gift-cards", base=ExportTask)
def export_gift_cards_task(
    export_file_id: int,
    scope: dict[str, Union[str, dict]],
    file_type: str,
    delimiter: str = ",",
):
    export_file = ExportFile.objects.get(pk=export_file_id)
    export_gift_cards(export_file, scope, file_type, delimiter)


@app.task(name="export-voucher-codes", base=ExportTask)
def export_voucher_codes_task(
    export_file_id: int,
    file_type: str,
    voucher_id: Optional[int],
    ids: list[int],
):
    export_file = ExportFile.objects.get(pk=export_file_id)
    export_voucher_codes(export_file, file_type, voucher_id, ids)


@app.task
def delete_old_export_files():
    now = timezone.now()

    events = ExportEvent.objects.filter(
        date__lte=now - settings.EXPORT_FILES_TIMEDELTA,
    ).values("export_file_id")
    export_files = ExportFile.objects.filter(
        Q(events__isnull=True) | Exists(events.filter(export_file_id=OuterRef("id")))
    )

    if not export_files:
        return

    paths_to_delete = list(export_files.values_list("content_file", flat=True))

    counter = 0
    for path in paths_to_delete:
        if path and default_storage.exists(path):
            default_storage.delete(path)
            counter += 1

    export_files.delete()

    task_logger.debug("Delete %s export files.", counter)
