from functools import partial

from django.db import migrations
from django.db.models import F, Q
from django.db.models.signals import post_migrate
from saleor.order.app import OrderAppConfig
from saleor.order.tasks import send_order_updated

BATCH_SIZE = 500


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


def set_order_line_base_prices(apps, schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        # The `post_migrate`` signal is sent once for every app migrated
        # we should execute it only once after update `order` module.
        if isinstance(sender, OrderAppConfig):
            order_ids = list(kwargs.get("updated_orders_pks"))
            send_order_updated.delay(order_ids)

    OrderLine = apps.get_model("order", "OrderLine")
    order_lines_to_update = OrderLine.objects.filter(
        ~Q(
            undiscounted_total_price_gross_amount=F(
                "undiscounted_unit_price_gross_amount"
            )
            * F("quantity")
        )
        | ~Q(
            undiscounted_total_price_net_amount=F("undiscounted_unit_price_net_amount")
            * F("quantity")
        )
    ).order_by("pk")
    updated_orders_pks = []
    for batch_pks in queryset_in_batches(order_lines_to_update):
        order_lines = OrderLine.objects.filter(pk__in=batch_pks)
        for order_line in order_lines:
            old_undiscounted_total_price_gross_amount = (
                order_line.undiscounted_total_price_gross_amount
            )
            old_undiscounted_total_price_net_amount = (
                order_line.undiscounted_total_price_net_amount
            )
            order_line.undiscounted_total_price_gross_amount = (
                order_line.undiscounted_unit_price_gross_amount * order_line.quantity
            )
            order_line.undiscounted_total_price_net_amount = (
                order_line.undiscounted_unit_price_net_amount * order_line.quantity
            )
            if (
                order_line.undiscounted_total_price_gross_amount
                != old_undiscounted_total_price_gross_amount
                or order_line.undiscounted_total_price_net_amount
                != old_undiscounted_total_price_net_amount
            ):
                updated_orders_pks.append(order_line.order_id)
        OrderLine.objects.bulk_update(
            order_lines,
            [
                "undiscounted_total_price_gross_amount",
                "undiscounted_total_price_net_amount",
            ],
        )

    # If we updated any order we should trigger `order_updated` after migrations
    if updated_orders_pks:
        updated_orders_pks = set(updated_orders_pks)
        post_migrate.connect(
            partial(on_migrations_complete, updated_orders_pks=updated_orders_pks),
            weak=False,
            dispatch_uid="send_order_updated",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0138_orderline_base_price"),
    ]

    operations = [
        migrations.RunPython(
            set_order_line_base_prices, reverse_code=migrations.RunPython.noop
        ),
    ]
