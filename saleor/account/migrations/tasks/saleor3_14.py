from django.db.models import Q, QuerySet, Case, When
from django.db import transaction

from ....celeryconf import app
from ...models import User

BATCH_SIZE = 5000


def set_user_is_confirmed(qs: QuerySet["User"]):
    is_confirmed_case = Case(
        When(
            Q(is_active=True) | Q(last_login__isnull=False),
            then=True,
        ),
        default=False,
    )
    with transaction.atomic():
        # lock the batch of objects
        _users = list(qs.select_for_update(of=(["self"])))
        qs.update(is_confirmed=is_confirmed_case)


@app.task
def set_user_is_confirmed_task():
    users = User.objects.order_by("-pk")
    ids = users.values_list("pk", flat=True)[:BATCH_SIZE]

    qs = User.objects.filter(pk__in=ids)

    if ids:
        set_user_is_confirmed(qs)
