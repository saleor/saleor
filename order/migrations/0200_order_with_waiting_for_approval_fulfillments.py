from django.db import migrations, transaction
from django.db.models import Exists, OuterRef

# The batch of size 250 takes ~0.2 second and consumes ~15MB memory at peak
BATCH_SIZE = 250


def migrate_orders_with_waiting_for_approval_fulfillment(apps, _schema_editor):
    Order = apps.get_model("order", "Order")
    Fulfillment = apps.get_model("order", "Fulfillment")

    waiting_for_approval_fulfillments = Fulfillment.objects.filter(
        status="waiting_for_approval"
    )
    fulfilled_fulfillments = Fulfillment.objects.filter(status="fulfilled")
    # get orders that has at least one waiting for approval fulfillment and not
    # fulfilled fulfillment
    qs = Order.objects.filter(
        Exists(waiting_for_approval_fulfillments.filter(order_id=OuterRef("id"))),
        ~Exists(fulfilled_fulfillments.filter(order_id=OuterRef("id"))),
        status="partially fulfilled",
    ).order_by("pk")
    for ids in queryset_in_batches(qs):
        orders = Order.objects.filter(id__in=ids).order_by("pk")
        with transaction.atomic():
            _orders_lock = list(orders.select_for_update(of=(["self"])))
            orders.update(status="unfulfilled")


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
        ("order", "0199_set_draft_base_price_expire_at"),
    ]

    operations = [
        migrations.RunPython(
            migrate_orders_with_waiting_for_approval_fulfillment,
            reverse_code=migrations.RunPython.noop,
        )
    ]
