import threading

import pytest
from django.db import transaction

from ..models import AppWebhookMutex
from ..utils import acquire_webhook_lock


def test_acquires_lock_when_mutex_row_exists(app):
    # given
    AppWebhookMutex.objects.create(app=app)

    # when
    with acquire_webhook_lock(app.id) as acquired:
        # then
        assert acquired is True


def test_creates_mutex_row_and_acquires_when_missing(app):
    # given
    assert not AppWebhookMutex.objects.filter(app_id=app.id).exists()

    # when
    with acquire_webhook_lock(app.id) as acquired:
        # then
        assert acquired is True

    assert AppWebhookMutex.objects.filter(app_id=app.id).count() == 1


@pytest.mark.django_db(transaction=True)
def test_does_not_acquire_when_lock_held_by_concurrent_transaction(
    app, django_db_blocker
):
    """Acquire the lock in a second thread, then assert the main thread is refused.

    `nowait=True` makes Postgres raise OperationalError immediately instead of
    blocking, which `acquire_webhook_lock` translates into `acquired = False`.
    """
    # given
    AppWebhookMutex.objects.create(app=app)

    lock_held = threading.Event()
    release_lock = threading.Event()

    def hold_lock():
        with django_db_blocker.unblock():
            with transaction.atomic():
                AppWebhookMutex.objects.select_for_update(
                    nowait=True, of=("self",)
                ).get(app_id=app.id)
                lock_held.set()
                # keep the row locked until the main thread has tried to acquire
                release_lock.wait(timeout=5)

    # opens database transaction and keeps it held until `release_lock` is set
    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert lock_held.wait(timeout=5), "background thread failed to acquire the lock"

    try:
        # when
        with acquire_webhook_lock(app.id) as acquired:
            # then
            assert acquired is False
    finally:
        release_lock.set()
        holder.join(timeout=5)
