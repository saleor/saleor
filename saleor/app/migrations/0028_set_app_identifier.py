from django.db import migrations
from django.db.models import F, QuerySet

from ..models import App

BATCH_SIZE = 1000


def queryset_in_batches(queryset):
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def set_app_identifier(qs: QuerySet["App"]):
    qs.update(identifier=F("uuid"))


def set_app_identifier_task(apps, _schema_editor):
    App = apps.get_model("app", "App")

    apps_qs = App.objects.filter(identifier__isnull=True).order_by("pk")

    for ids in queryset_in_batches(apps_qs):
        qs = App.objects.filter(pk__in=ids)
        set_app_identifier(qs)


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0027_set_identifier_when_missing"),
    ]

    operations = [
        migrations.RunPython(set_app_identifier_task, migrations.RunPython.noop)
    ]
