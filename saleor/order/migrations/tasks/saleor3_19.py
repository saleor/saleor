from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q
from django.forms.models import model_to_dict

from ....account.models import Address
from ....celeryconf import app
from ....discount.models import OrderDiscount, Voucher
from ....warehouse.models import Warehouse
from ...models import Order, OrderLine

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250

# The batch of size 250 takes ~0.3 second and consumes ~30MB memory at peak
ORDER_CALCULATE_SHIPPING_PRICE_BATCH_SIZE = 500

# The batch of size 250 takes ~0.3 second and consumes ~20MB memory at peak
ORDER_SET_SHIPPING_PRICE_BATCH_SIZE = 1000


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
        update_order_addresses_task()


@app.task
def set_udniscounted_base_shipping_price_on_orders_task():
    migrate_orders_with_voucher_instance.delay()


@app.task
def migrate_orders_with_voucher_instance():
    shipping_vouchers = Voucher.objects.filter(type="shipping")
    orders = Order.objects.filter(
        undiscounted_base_shipping_price_amount__isnull=True,
        origin__in=["checkout"],
        voucher_code__isnull=False,
        voucher__isnull=False,
    ).filter(Exists(shipping_vouchers.filter(pk=OuterRef("voucher_id"))))

    order_ids = list(
        orders.values_list("pk", flat=True)[:ORDER_CALCULATE_SHIPPING_PRICE_BATCH_SIZE]
    )
    if order_ids:
        calculate_and_set_undiscounted_base_shipping_price(order_ids)
        migrate_orders_with_voucher_instance.delay()
    else:
        migrate_orders_no_voucher_instance.delay()


@app.task
def migrate_orders_no_voucher_instance():
    # lines with applied line voucher
    lines_with_voucher = OrderLine.objects.filter(voucher_code__isnull=False)

    # lines without applied order voucher on line
    # this excludes the cases when entire order voucher was applied
    # (for `ENTIRE_ORDER` voucher type, the voucher_code is stored on the order itself,
    # not on the line, but the discount is propagated to the line level and it's visible
    # in the `unit_price`)
    # - `base_unit_price_amount` is the price with the sale and line voucher applied
    # - `unit_price` is the price with all discounts applied - sales,
    # line and order voucher
    lines_with_not_applicable_voucher = OrderLine.objects.filter(
        Q(voucher_code__isnull=True)
        & (
            Q(base_unit_price_amount=F("unit_price_net_amount"))
            | Q(base_unit_price_amount=F("unit_price_gross_amount"))
        )
    )

    # orders with voucher code, no voucher instance, without line vouchers
    # and not applicable order voucher
    orders = (
        Order.objects.filter(
            undiscounted_base_shipping_price_amount__isnull=True,
            origin__in=["checkout"],
            voucher_code__isnull=False,
            voucher__isnull=True,
        )
        .exclude(Exists(lines_with_voucher.filter(order_id=OuterRef("pk"))))
        .filter(
            Exists(lines_with_not_applicable_voucher.filter(order_id=OuterRef("pk")))
        )
    )

    order_ids = list(
        orders.values_list("pk", flat=True)[:ORDER_CALCULATE_SHIPPING_PRICE_BATCH_SIZE]
    )
    if order_ids:
        calculate_and_set_undiscounted_base_shipping_price(order_ids)
        migrate_orders_no_voucher_instance.delay()
    else:
        set_undiscounted_base_shipping_price_shipping_price_same_as_base.delay()


def calculate_and_set_undiscounted_base_shipping_price(order_ids):
    orders = Order.objects.filter(id__in=order_ids)
    order_discounts = OrderDiscount.objects.filter(
        order_id__in=orders.values("pk"), type="voucher"
    )
    order_to_discount_amount = {
        order_discount["order_id"]: order_discount["amount_value"]
        for order_discount in order_discounts.values("order_id", "amount_value")
    }
    for order in orders:
        order.undiscounted_base_shipping_price_amount = (
            order.base_shipping_price_amount + order_to_discount_amount[order.pk]
        )
    with transaction.atomic():
        _orders = list(orders.select_for_update(of=(["self"])))
        Order.objects.bulk_update(orders, ["undiscounted_base_shipping_price_amount"])


@app.task
def set_undiscounted_base_shipping_price_shipping_price_same_as_base():
    qs = Order.objects.filter(Q(undiscounted_base_shipping_price_amount__isnull=True))
    order_ids = qs.values_list("pk", flat=True)[:ORDER_SET_SHIPPING_PRICE_BATCH_SIZE]
    if order_ids:
        set_undiscounted_base_shipping_price(order_ids)
        set_undiscounted_base_shipping_price_shipping_price_same_as_base.delay()


def set_undiscounted_base_shipping_price(order_ids):
    orders = Order.objects.filter(id__in=order_ids)
    with transaction.atomic():
        _orders = list(orders.select_for_update(of=(["self"])))
        orders.update(
            undiscounted_base_shipping_price_amount=F("base_shipping_price_amount")
        )
