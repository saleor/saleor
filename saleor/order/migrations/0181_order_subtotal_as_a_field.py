from django.db import migrations
from django.db.models import Exists, F, Func, OuterRef, Subquery

# One batch took 0.1s and 10.54MB at its peak
BATCH_SIZE = 1000


def update_order_subtotals(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    OrderLine = apps.get_model("order", "OrderLine")

    first_order = Order.objects.last()
    if first_order is None:
        return  # Exit if there are no orders
    start_number = first_order.number

    while True:
        # right here we need to find only Orders which was not populated
        # with subtotal in previous release, so the amount of rows to populate
        # shouldn't be big
        lines = OrderLine.objects.all()
        queryset = Order.objects.order_by("number").filter(
            Exists(lines.filter(order_id=OuterRef("id"))),
            number__gte=start_number,
            subtotal_gross_amount__exact=0,
        )[:BATCH_SIZE]
        current_batch_order_numbers = list(queryset.values_list("number", flat=True))

        # Break the loop if there are no orders
        if not current_batch_order_numbers:
            break

        order_line = OrderLine.objects.filter(order=OuterRef("pk"))
        subtotal_net_sum = order_line.annotate(
            net_sum=Func(F("total_price_net_amount"), function="Sum")
        ).values("net_sum")

        subtotal_gross_sum = order_line.annotate(
            gross_sum=Func(F("total_price_gross_amount"), function="Sum")
        ).values("gross_sum")

        orders_with_totals = Order.objects.filter(
            number__in=current_batch_order_numbers
        ).annotate(
            subtotal_net_sum=Subquery(subtotal_net_sum),
            subtotal_gross_sum=Subquery(subtotal_gross_sum),
        )

        orders_to_update = []
        for order in orders_with_totals:
            order.subtotal_net_amount = order.subtotal_net_sum
            order.subtotal_gross_amount = order.subtotal_gross_sum
            orders_to_update.append(order)

        Order.objects.bulk_update(
            orders_to_update, ["subtotal_net_amount", "subtotal_gross_amount"]
        )
        start_number = current_batch_order_numbers[-1]


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0180_auto_20231108_0908"),
    ]

    operations = [
        migrations.RunPython(
            update_order_subtotals, reverse_code=migrations.RunPython.noop
        ),
    ]
