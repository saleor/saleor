from typing import Dict, Union

from ..celeryconf import app
from ..core import JobStatus
from . import events
from .emails import send_export_failed_info
from .models import ExportFile
from .utils.export import export_products


def on_task_failure(self, exc, task_id, args, kwargs, einfo):
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

    if export_file.user:
        send_export_failed_info(export_file, export_file.user.email, "export_failed")


def on_task_success(self, retval, task_id, args, kwargs):
    export_file_id = args[0]

    export_file = ExportFile.objects.get(pk=export_file_id)
    export_file.status = JobStatus.SUCCESS
    export_file.save(update_fields=["status", "updated_at"])

    events.export_success_event(
        export_file=export_file, user=export_file.user, app=export_file.app
    )


@app.task(on_success=on_task_success, on_failure=on_task_failure)
def export_products_task(
    export_file_id: int,
    scope: Dict[str, Union[str, dict]],
    export_info: Dict[str, list],
    file_type: str,
    delimiter: str = ";",
):
    export_file = ExportFile.objects.get(pk=export_file_id)
    export_products(export_file, scope, export_info, file_type, delimiter)
