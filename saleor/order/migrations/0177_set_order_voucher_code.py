from django.db import migrations
from django.db.models import Exists, OuterRef

# The batch took about 0.3s and consumes ~10MB memory at peak
BATCH_SIZE = 1000


def queryset_in_batches(queryset):
    start_pk = 0

    while True:
        qs = queryset.order_by("pk").filter(pk__gt=start_pk)[:BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def set_order_voucher_code(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    Voucher = apps.get_model("discount", "Voucher")
    orders = Order.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")
    for ids in queryset_in_batches(orders):
        qs = Order.objects.filter(pk__in=ids)
        set_voucher_code(Order, Voucher, qs)


def set_voucher_code(Order, Voucher, orders):
    vouchers_to_code = get_voucher_id_to_code_map(Voucher, orders)
    orders_list = []
    for order in orders:
        code = vouchers_to_code[order.voucher_id]
        order.voucher_code = code
        orders_list.append(order)
    Order.objects.bulk_update(orders_list, ["voucher_code"])


def get_voucher_id_to_code_map(Voucher, orders):
    vouchers = Voucher.objects.filter(Exists(orders.filter(voucher_id=OuterRef("pk"))))
    voucher_id_to_code_map = {
        voucher_id: code for voucher_id, code in vouchers.values_list("id", "code")
    }
    return voucher_id_to_code_map


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0056_voucher_code_indexes"),
        ("order", "0176_order_voucher_code_add_index"),
    ]

    run_before = [
        ("discount", "0066_clear_voucher_and_vouchercustomer"),
    ]

    operations = [
        migrations.RunPython(
            set_order_voucher_code,
            migrations.RunPython.noop,
        ),
    ]
