from celery.utils.log import get_task_logger
from django.conf import settings

from ....celeryconf import app
from ....core.db.connection import allow_writer
from ....permission.enums import AppPermission
from ....permission.models import Permission
from ...models import App, AppExtension

REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE = 1000
REMOVE_MANAGE_APPS_PERMISSION_MAX_DEPTH = 10000


task_logger = get_task_logger(f"{__name__}.celery")


def _get_manage_apps_permission() -> Permission | None:
    return Permission.objects.filter(
        codename=AppPermission.MANAGE_APPS.codename,
        content_type__app_label="app",
    ).first()


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def remove_manage_apps_permission_from_apps_task(
    current_depth: int = 0,
    max_depth: int = REMOVE_MANAGE_APPS_PERMISSION_MAX_DEPTH,
):
    if current_depth > max_depth:
        raise RecursionError(
            f"Data migration removing MANAGE_APPS from apps has recursed "
            f"{current_depth} times. Is the job stuck? Rerun this task manually "
            f"with a higher max_depth if there is a lot of data to delete."
        )

    manage_apps = _get_manage_apps_permission()
    if manage_apps is None:
        return

    through = App.permissions.through
    inner_pks = list(
        through.objects.filter(permission=manage_apps)
        .order_by("pk")
        .values_list("pk", flat=True)[:REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE]
    )
    if not inner_pks:
        return

    deleted_count, _ = through.objects.filter(pk__in=inner_pks).delete()
    task_logger.info("Removed MANAGE_APPS from %d App rows", deleted_count)

    if len(inner_pks) == REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE:
        remove_manage_apps_permission_from_apps_task.delay(
            current_depth=current_depth + 1, max_depth=max_depth
        )


@app.task(queue=settings.DATA_MIGRATIONS_TASKS_QUEUE_NAME)
@allow_writer()
def remove_manage_apps_permission_from_app_extensions_task(
    current_depth: int = 0,
    max_depth: int = REMOVE_MANAGE_APPS_PERMISSION_MAX_DEPTH,
):
    if current_depth > max_depth:
        raise RecursionError(
            f"Data migration removing MANAGE_APPS from app extensions has "
            f"recursed {current_depth} times. Is the job stuck? Rerun this task "
            f"manually with a higher max_depth if there is a lot of data to "
            f"delete."
        )

    manage_apps = _get_manage_apps_permission()
    if manage_apps is None:
        return

    through = AppExtension.permissions.through
    inner_pks = list(
        through.objects.filter(permission=manage_apps)
        .order_by("pk")
        .values_list("pk", flat=True)[:REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE]
    )
    if not inner_pks:
        return

    deleted_count, _ = through.objects.filter(pk__in=inner_pks).delete()
    task_logger.info("Removed MANAGE_APPS from %d AppExtension rows", deleted_count)

    if len(inner_pks) == REMOVE_MANAGE_APPS_PERMISSION_BATCH_SIZE:
        remove_manage_apps_permission_from_app_extensions_task.delay(
            current_depth=current_depth + 1, max_depth=max_depth
        )
