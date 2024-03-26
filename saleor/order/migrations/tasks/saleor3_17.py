from ....celeryconf import app
from ...models import Order
from ....discount.models import Voucher
from django.db.models import Exists, OuterRef
from django.db import transaction
from ....account.models import Address
from ....warehouse.models import Warehouse
from django.forms.models import model_to_dict


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

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250


@app.task
def set_order_voucher_code_task():
    orders = Order.objects.filter(
        voucher__isnull=False, voucher_code__isnull=True
    ).order_by("pk")[:BATCH_SIZE]
    if ids := list(orders.values_list("pk", flat=True)):
        qs = Order.objects.filter(pk__in=ids)
        with transaction.atomic():
            _orders = list(qs.select_for_update(of=(["self"])))
            set_voucher_code(qs)
        set_order_voucher_code_task.delay()


def set_voucher_code(orders):
    vouchers_to_code = get_voucher_id_to_code_map(orders)
    orders_list = []
    for order in orders:
        code = vouchers_to_code[order.voucher_id]
        order.voucher_code = code
        orders_list.append(order)
    Order.objects.bulk_update(orders_list, ["voucher_code"])


def get_voucher_id_to_code_map(orders):
    vouchers = Voucher.objects.filter(Exists(orders.filter(voucher_id=OuterRef("pk"))))
    voucher_id_to_code_map = {
        voucher_id: code for voucher_id, code in vouchers.values_list("id", "code")
    }
    return voucher_id_to_code_map


@app.task
def update_order_addresses_task():
    qs = Order.objects.filter(
        Exists(Warehouse.objects.filter(address_id=OuterRef("shipping_address_id"))),
    )
    order_ids = qs.values_list("pk", flat=True)[:ADDRESS_UPDATE_BATCH_SIZE]
    addresses = []
    if order_ids:
        orders = Order.objects.filter(id__in=order_ids)
        for order in orders:
            if cc_address := order.shipping_address:
                order_address = Address(**model_to_dict(cc_address, exclude=["id"]))
                order.shipping_address = order_address
                addresses.append(order_address)
        Address.objects.bulk_create(addresses, ignore_conflicts=True)
        Order.objects.bulk_update(orders, ["shipping_address"])
        update_order_addresses_task.delay()
