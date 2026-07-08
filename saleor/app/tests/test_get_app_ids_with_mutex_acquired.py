import threading

import pytest
from django.db import transaction

from ..models import AppWebhookMutex
from ..utils import get_app_ids_with_mutex_acquired


def test_reports_no_apps_when_no_lock_is_held(app):
    # given
    AppWebhookMutex.objects.create(app=app)

    # when
    busy_app_ids = get_app_ids_with_mutex_acquired([app.id])

    # then
    assert busy_app_ids == set()


def test_reports_app_without_mutex_row_as_free(app):
    # given
    assert not AppWebhookMutex.objects.filter(app_id=app.id).exists()

    # when
    busy_app_ids = get_app_ids_with_mutex_acquired([app.id])

    # then
    assert busy_app_ids == set()


@pytest.mark.django_db(transaction=True)
def test_reports_app_with_lock_held_by_concurrent_transaction(app, django_db_blocker):
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
                # keep the row locked until the main thread has run the probe
                release_lock.wait(timeout=5)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert lock_held.wait(timeout=5), "background thread failed to acquire the lock"

    try:
        # when
        busy_app_ids = get_app_ids_with_mutex_acquired([app.id])
    finally:
        release_lock.set()
        holder.join(timeout=5)

    # then
    assert busy_app_ids == {app.id}
