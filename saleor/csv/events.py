from typing import TYPE_CHECKING

from ..account.models import User
from . import ExportEvents
from .models import ExportEvent

if TYPE_CHECKING:
    from .models import ExportFile


def data_export_event(*, export_file: "ExportFile", user: User):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.DATA_EXPORT_PENDING
    )


def data_export_success_event(*, export_file: "ExportFile", user: User):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.DATA_EXPORT_SUCCESS
    )


def data_export_failed_event(*, export_file: "ExportFile", user: User, message: str):
    ExportEvent.objects.create(
        export_file=export_file,
        user=user,
        type=ExportEvents.DATA_EXPORT_FAILED,
        parameters={"message": message},
    )


def data_export_deleted_event(*, export_file: "ExportFile", user: User):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.DATA_EXPORT_DELETED
    )


def export_file_sent_event(*, export_file: "ExportFile", user: User):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.EXPORTED_FILE_SENT
    )
