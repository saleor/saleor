# Generated by Django 4.2.16 on 2025-03-05 11:21
from datetime import timedelta

from django.db import migrations, transaction
from django.db.models import Exists, OuterRef
from django.utils import timezone

# The batch of size 250 takes ~0.2 second and consumes ~20MB memory at peak
BATCH_SIZE = 250
DEFAULT_EXPIRE_TIME = 24


def set_base_price_expire_time(apps, _schema_editor):
    Order = apps.get_model("order", "Order")
    OrderLine = apps.get_model("order", "OrderLine")
    orders = Order.objects.filter(status="draft")
    qs = (
        OrderLine.objects.filter(Exists(orders.filter(pk=OuterRef("order_id"))))
        .filter(draft_base_price_expire_at__isnull=True)
        .order_by("pk")
    )
    now = timezone.now()
    expire_time = now + timedelta(hours=DEFAULT_EXPIRE_TIME)
    for ids in queryset_in_batches(qs):
        order_lines = OrderLine.objects.filter(id__in=ids).order_by("pk")
        with transaction.atomic():
            _order_lines_lock = list(order_lines.select_for_update(of=(["self"])))
            order_lines.update(draft_base_price_expire_at=expire_time)


def queryset_in_batches(queryset):
    start_pk = 0
    while True:
        qs = queryset.filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))
        if not pks:
            break
        yield pks
        start_pk = pks[-1]


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0198_orderline_draft_base_price_expire_at"),
    ]

    operations = [
        migrations.RunPython(
            set_base_price_expire_time,
            reverse_code=migrations.RunPython.noop,
        )
    ]
