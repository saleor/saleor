from enum import IntEnum

from django.conf import settings
from django.db import transaction
from django.utils.module_loading import import_string

# Arbitrary 32-bit integer identifying Saleor's advisory locks globally within a database.
ADVISORY_LOCK_NAMESPACE = 21_218


class AdvisoryLock(IntEnum):
    """Advisory lock keys. Never reuse or renumber values."""

    CATEGORY_TREE = 1
    MENU_ITEM_TREE = 2


def get_advisory_lock_namespace() -> int:
    if settings.ADVISORY_LOCK_NAMESPACE_IMPORT is not None:
        return import_string(settings.ADVISORY_LOCK_NAMESPACE_IMPORT)()
    return ADVISORY_LOCK_NAMESPACE


def acquire_advisory_xact_lock(lock: AdvisoryLock) -> None:
    """Block until the transaction-scoped advisory lock is acquired.

    Auto-released on commit/rollback (pgbouncer-safe). Must be called inside
    an atomic block, before any `select_for_update` row locks.
    """
    connection = transaction.get_connection()
    if not connection.in_atomic_block:
        raise RuntimeError(
            "acquire_advisory_xact_lock must be called inside an atomic block."
        )
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(%s, %s)",
            [get_advisory_lock_namespace(), lock.value],
        )
