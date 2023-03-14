from decimal import Decimal

from django.db import migrations

BATCH_SIZE = 10000


def add_tax_to_undiscounted_price(
    price, prices_entered_with_tax, tax_rate
):
    untaxed_price = price.net
    tax_rate = Decimal(1 + tax_rate)

    if prices_entered_with_tax:
        net_amount = untaxed_price.amount / tax_rate
        gross_amount = untaxed_price.amount
    else:
        net_amount = untaxed_price.amount
        gross_amount = untaxed_price.amount * tax_rate
    price.net.amount = net_amount
    price.gross.amount = gross_amount


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


def recalculate_tax_to_price(price, prices_entered_with_tax, tax_rate):
    net_amount = price.net_amount_field
    gross_amount = price.gross_amount_field
    if net_amount == gross_amount and all([net_amount != 0, gross_amount != 0]):
        add_tax_to_undiscounted_price(
            price,
            prices_entered_with_tax,
            tax_rate
        )


def recalculate_undiscounted_prices_for_order(apps, _schema_editor):
    OrderLine = apps.get_model("order", "OrderLine")
    queryset = OrderLine.objects.all()
    for batch_pks in queryset_in_batches(queryset):
        order_lines = OrderLine.objects.filter(pk__in=batch_pks)
        for line in order_lines:
            prices_entered_with_tax = (
                line.order.channel.tax_configuration.prices_entered_with_tax
            )
            tax_rate = line.tax_rate
            recalculate_tax_to_price(
                line.undiscounted_unit_price, prices_entered_with_tax, tax_rate
            )
            recalculate_tax_to_price(
                line.undiscounted_total_price, prices_entered_with_tax, tax_rate
            )
            line.save(
                update_fields=["undiscounted_unit_price", "undiscounted_total_price"]
            )


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0160_merge_20221215_1253"),
    ]

    operations = [
        migrations.RunPython(
            recalculate_undiscounted_prices_for_order,
            reverse_code=migrations.RunPython.noop
        ),
    ]
