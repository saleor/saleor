import datetime
from collections.abc import Iterable

from django.utils import timezone

from ..core.tracing import traced_atomic_transaction
from .lock_objects import app_problem_qs_select_for_update, app_qs_select_for_update
from .models import AppProblem

MESSAGE_MAX_LENGTH = 2048
DEFAULT_AGGREGATION_PERIOD = 60


def truncate_message(message: str) -> str:
    """Truncate a problem message to the length the column accepts."""
    if len(message) > MESSAGE_MAX_LENGTH:
        return message[: MESSAGE_MAX_LENGTH - 3] + "..."
    return message


def create_or_update_problem(
    app_id: int,
    *,
    message: str,
    key: str,
    critical_threshold: int | None = None,
    aggregation_period: int = DEFAULT_AGGREGATION_PERIOD,
    now: datetime.datetime | None = None,
) -> AppProblem:
    """Report a problem for an app, aggregating it with a recent one under the same key.

    A problem raised within ``aggregation_period`` minutes of the last undismissed
    problem with the same key bumps that problem's count instead of creating a new row.
    An ``aggregation_period`` of 0 always creates a new problem. The problem becomes
    critical once its count reaches ``critical_threshold``; without a threshold it never
    escalates.
    """
    now = now or timezone.now()
    message = truncate_message(message)

    with traced_atomic_transaction():
        # Lock the App row to serialize all problem operations for this app.
        # At this point it trades performance for correctness. If we need to improve
        # performance, we can skip locking entire app row and schedule a cleanup task
        # for > MAX_PROBLEMS_PER_APP items.
        app_qs_select_for_update().filter(pk=app_id).first()

        existing = (
            AppProblem.objects.filter(app_id=app_id, key=key, dismissed=False)
            .order_by("-updated_at")
            .first()
        )

        if existing and aggregation_period > 0:
            cutoff = now - datetime.timedelta(minutes=aggregation_period)
            if existing.updated_at >= cutoff:
                _aggregate_existing(existing, message, critical_threshold, now)
                return existing

        return _create_new_problem(app_id, message, key, critical_threshold)


def _aggregate_existing(
    existing: AppProblem,
    message: str,
    critical_threshold: int | None,
    now: datetime.datetime,
) -> None:
    # In transaction block - we can safely modify in memory
    existing.count += 1
    existing.is_critical = bool(
        critical_threshold and existing.count >= critical_threshold
    )
    existing.message = message
    existing.updated_at = now
    existing.save(update_fields=["count", "updated_at", "message", "is_critical"])


def _create_new_problem(
    app_id: int,
    message: str,
    key: str,
    critical_threshold: int | None,
) -> AppProblem:
    total_count = AppProblem.objects.filter(app_id=app_id).count()
    # +1 accounts for the new problem we're about to create
    excess_count = total_count - AppProblem.MAX_PROBLEMS_PER_APP + 1

    if excess_count > 0:
        oldest_pks = list(
            AppProblem.objects.filter(app_id=app_id)
            .order_by("updated_at")
            .values_list("pk", flat=True)[:excess_count]
        )
        if oldest_pks:
            AppProblem.objects.filter(pk__in=oldest_pks).delete()

    return AppProblem.objects.create(
        app_id=app_id,
        message=message,
        key=key,
        count=1,
        is_critical=bool(critical_threshold and critical_threshold <= 1),
    )


def dismiss_problems_by_keys(app_id: int, keys: Iterable[str]) -> None:
    """Dismiss every undismissed problem of an app stored under the given keys.

    Problems are dismissed rather than deleted so the app's history is preserved.
    """
    with traced_atomic_transaction():
        pks = (
            app_problem_qs_select_for_update()
            .filter(app_id=app_id, key__in=keys, dismissed=False)
            .values_list("pk", flat=True)
        )
        AppProblem.objects.filter(pk__in=pks).update(dismissed=True)
