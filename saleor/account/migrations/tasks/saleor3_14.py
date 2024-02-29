from django.db.models import QuerySet
from django.db import transaction

from ....celeryconf import app
from ...models import User

# Batch size of 5000 is about ~8MB of memory usage
BATCH_SIZE = 5000


def set_user_is_confirmed_to_false(qs: QuerySet["User"]):
    with transaction.atomic():
        # lock the batch of objects
        _users = list(qs.select_for_update(of=(["self"])))
        qs.update(is_confirmed=False)


@app.task
def set_user_is_confirmed_task():
    users = User.objects.order_by("pk").filter(is_confirmed=True)
    users = users.filter(is_active=False, last_login__isnull=True)
    ids = users.values_list("pk", flat=True)[:BATCH_SIZE]

    qs = User.objects.filter(pk__in=ids)
    if ids:
        set_user_is_confirmed_to_false(qs)
        set_user_is_confirmed_task.delay()


def set_user_is_confirmed_to_true(qs: QuerySet["User"]):
    with transaction.atomic():
        # lock the batch of objects
        _users = list(qs.select_for_update(of=(["self"])))
        qs.update(is_confirmed=True)


@app.task
def confirm_active_users_task():
    users = User.objects.order_by("pk").filter(
        is_confirmed=False, is_active=True, last_login__isnull=False
    )
    ids = users.values_list("pk", flat=True)[:BATCH_SIZE]

    qs = User.objects.filter(pk__in=ids)
    if ids:
        set_user_is_confirmed_to_true(qs)
        confirm_active_users_task.delay()
