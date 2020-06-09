from typing import TYPE_CHECKING, Optional

from ..account.models import User
from . import ExportEvents
from .models import ExportEvent

if TYPE_CHECKING:
    from .models import ExportFile
    from ..app.models import App

UserType = Optional[User]


def export_started_event(
    *, export_file: "ExportFile", user: UserType = None, app: "App" = None
):
    ExportEvent.objects.create(
        export_file=export_file, user=user, app=app, type=ExportEvents.EXPORT_PENDING
    )


def export_success_event(
    *, export_file: "ExportFile", user: UserType = None, app: "App" = None
):
    ExportEvent.objects.create(
        export_file=export_file, user=user, app=app, type=ExportEvents.EXPORT_SUCCESS
    )


def export_failed_event(
    *,
    export_file: "ExportFile",
    user: UserType = None,
    app: "App" = None,
    message: str,
    error_type: str
):
    ExportEvent.objects.create(
        export_file=export_file,
        user=user,
        app=app,
        type=ExportEvents.EXPORT_FAILED,
        parameters={"message": message, "error_type": error_type},
    )


def export_deleted_event(
    *, export_file: "ExportFile", user: UserType = None, app: "App" = None
):
    ExportEvent.objects.create(
        export_file=export_file, user=user, app=app, type=ExportEvents.EXPORT_DELETED
    )


def export_file_sent_event(*, export_file: "ExportFile", user: UserType):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.EXPORTED_FILE_SENT
    )


def export_failed_info_sent_event(*, export_file: "ExportFile", user: UserType):
    ExportEvent.objects.create(
        export_file=export_file, user=user, type=ExportEvents.EXPORT_FAILED_INFO_SENT
    )
