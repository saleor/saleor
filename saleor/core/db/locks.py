from enum import IntEnum

from django.db import transaction

# Arbitrary fixed namespace for Saleor's advisory locks.
ADVISORY_LOCK_NAMESPACE = 21_218


class AdvisoryLock(IntEnum):
    """Advisory lock keys. Never reuse or renumber values."""

    CATEGORY_TREE = 1
    MENU_ITEM_TREE = 2


def acquire_advisory_xact_lock(lock: AdvisoryLock, using: str | None = None) -> None:
    """Block until the transaction-scoped advisory lock is acquired.

    Auto-released on commit/rollback (pgbouncer-safe). Must be called inside
    an atomic block, before any `select_for_update` row locks.
    """
    connection = transaction.get_connection(using)
    if not connection.in_atomic_block:
        raise RuntimeError(
            "acquire_advisory_xact_lock must be called inside an atomic block."
        )
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s, %s)",
            [ADVISORY_LOCK_NAMESPACE, lock.value],
        )
