from django.db import migrations, transaction
from django.db.models import Q, QuerySet, Case, When
from ..models import User


BATCH_SIZE = 5000


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


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


def set_user_is_confirmed_task(apps, schema_editor):
    User = apps.get_model("account", "User")
    users = User.objects.order_by("pk")

    for ids in queryset_in_batches(users):
        qs = User.objects.filter(pk__in=ids)
        set_user_is_confirmed(qs)


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0080_user_is_confirmed"),
    ]

    operations = [
        migrations.RunPython(set_user_is_confirmed_task, migrations.RunPython.noop)
    ]
