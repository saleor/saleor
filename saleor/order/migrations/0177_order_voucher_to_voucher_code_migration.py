from django.db import migrations
from django.db.models import Exists, OuterRef

# For batch size 1000 with 2000 per model Order/Voucher/VoucherCode objects
# Migration took 0.65 seconds.
# Memory usage increased by 10.18 MiB.

# For batch size 1000 with 1000 per model Order/Voucher/VoucherCode objects
# (in the future one celery task)
# Migration took 0.39 seconds.
# Memory usage increased by 3.30 MiB.

# For batch size 1000 with 100_000 per model Order/Voucher/VoucherCode objects
# Migration took 46.44 seconds.
# Memory usage increased by 294.54 MiB.


BATCH_SIZE = 1000


def set_voucher_to_voucher_code_in_order(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    Voucher = apps.get_model("discount", "Voucher")
    VoucherCode = apps.get_model("discount", "VoucherCode")
    set_voucher_to_voucher_code(Order, Voucher, VoucherCode)


def set_voucher_to_voucher_code(Order, Voucher, VoucherCode) -> None:
    orders = Order.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BATCH_SIZE]
    if ids := list(orders.values_list("pk", flat=True)):
        qs = Order.objects.filter(pk__in=ids)
        set_voucher_code(Order, Voucher, VoucherCode, qs)
        set_voucher_to_voucher_code(Order, Voucher, VoucherCode)


def set_voucher_code(Order, Voucher, VoucherCode, orders) -> None:
    voucher_id_to_code_map = get_voucher_id_to_code_map(Voucher, VoucherCode, orders)
    orders_list = []
    for order in orders:
        code = voucher_id_to_code_map[order.voucher_id]
        order.voucher_code = code
        orders_list.append(order)
    Order.objects.bulk_update(orders_list, ["voucher_code"])


def get_voucher_id_to_code_map(Voucher, VoucherCode, orders) -> None:
    voucher_id_to_code_map = {}
    vouchers = Voucher.objects.filter(Exists(orders.filter(voucher_id=OuterRef("pk"))))
    codes = VoucherCode.objects.filter(
        Exists(vouchers.filter(id=OuterRef("voucher_id")))
    )
    for code in codes:
        voucher_id_to_code_map[code.voucher_id] = code.code

    return voucher_id_to_code_map


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0065_orderdiscount_voucher_code_add_index"),
        ("order", "0176_order_voucher_code_add_index"),
    ]

    operations = [
        migrations.RunPython(
            set_voucher_to_voucher_code_in_order,
            migrations.RunPython.noop,
        ),
    ]
