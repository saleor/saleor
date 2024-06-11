from django.db import transaction
from django.db.models import F, Q, QuerySet

from ....celeryconf import app
from ...models import Address, User

# Batch size of 5000 is about ~8MB of memory usage
BATCH_SIZE = 5000


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


@app.task
def set_invalid_format_task():
    addresses = (
        Address.objects.filter(~Q(validation_skipped=F("invalid_format")))
        .only("pk", "validation_skipped", "invalid_format")
        .order_by("pk")
    )
    ids = addresses.values_list("pk", flat=True)[:BATCH_SIZE]
    if ids:
        qs = Address.objects.filter(pk__in=ids)
        with transaction.atomic():
            _lock = list(qs.select_for_update(of=(["self"])))
            qs.update(invalid_format=F("validation_skipped"))
        set_invalid_format_task.delay()
