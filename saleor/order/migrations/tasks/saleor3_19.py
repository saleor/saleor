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

ORDER_UPDATE_BATCH_SIZE = 100


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


@app.task
def set_udniscounted_base_shipping_price_on_orders_task():
    set_undiscounted_base_shipping_price_shipping_price_same_as_base.delay()
    migrate_orders_with_voucher_instance.delay()
    migrate_orders_no_voucher_instance.delay()


@app.task
def set_undiscounted_base_shipping_price_shipping_price_same_as_base():
    lines_with_voucher = OrderLine.objects.filter(voucher_code__isnull=False)
    qs = Order.objects.filter(
        Q(undiscounted_base_shipping_price__isnull=True)
        & (
            # draft orders
            Q(status="draft")
            # orders created from draft or by bulk create
            | Q(origin__in=["draft", "bulk_create"])
            # orders from checkout without voucher code
            | Q(origin__in=["checkout"], voucher_code__isnull=True)
            # orders from checkout with voucher, voucher applied on lines
            | (
                Q(origin__in=["checkout"], voucher_code__isnull=False)
                & Exists(lines_with_voucher.filter(order_id=OuterRef("pk")))
            )
        )
    )
    order_ids = qs.values_list("pk", flat=True)[:ORDER_UPDATE_BATCH_SIZE]
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


@app.task
def migrate_orders_with_voucher_instance():
    shipping_vouchers = Voucher.objects.filter(type="shipping")
    qs = Order.objects.filter(
        undiscounted_base_shipping_price__isnull=True,
        origin__in=["checkout"],
        voucher_code__isnull=False,
        voucher__isnull=False,
    )

    orders_with_shipping_voucher = qs.filter(
        Exists(shipping_vouchers.filter(pk=OuterRef("voucher_id")))
    )
    order_with_another_vouchers = qs.exclude(
        Exists(shipping_vouchers.filter(pk=OuterRef("voucher_id")))
    )

    orders_with_shipping_voucher_ids = list(
        orders_with_shipping_voucher.values_list("pk", flat=True)[
            :ORDER_UPDATE_BATCH_SIZE
        ]
    )
    if orders_with_shipping_voucher_ids:
        calculate_and_set_undiscounted_base_shipping_price(
            orders_with_shipping_voucher_ids
        )

    order_with_another_vouchers_ids = list(
        order_with_another_vouchers.values_list("pk", flat=True)[
            :ORDER_UPDATE_BATCH_SIZE
        ]
    )
    if order_with_another_vouchers_ids:
        set_undiscounted_base_shipping_price(order_with_another_vouchers_ids)

    if orders_with_shipping_voucher_ids or order_with_another_vouchers_ids:
        migrate_orders_with_voucher_instance.delay()


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
    orders = Order.objects.filter(
        undiscounted_base_shipping_price__isnull=True,
        origin__in=["checkout"],
        voucher_code__isnull=False,
        voucher__isnull=True,
    ).exclude(Exists(lines_with_voucher.filter(order_id=OuterRef("pk"))))
    # find orders with not line vouchers and not applicable order voucher
    orders_with_shipping_discount = orders.filter(
        Exists(lines_with_not_applicable_voucher.filter(order_id=OuterRef("pk")))
    )

    orders_no_shipping_discount = orders.exclude(
        Exists(lines_with_not_applicable_voucher.filter(order_id=OuterRef("pk")))
    )

    order_shipping_discount_ids = list(
        orders_with_shipping_discount.values_list("pk", flat=True)[
            :ORDER_UPDATE_BATCH_SIZE
        ]
    )
    if order_shipping_discount_ids:
        calculate_and_set_undiscounted_base_shipping_price(order_shipping_discount_ids)

    order_no_shipping_discount_ids = list(
        orders_no_shipping_discount.values_list("pk", flat=True)[
            :ORDER_UPDATE_BATCH_SIZE
        ]
    )
    if order_no_shipping_discount_ids:
        set_undiscounted_base_shipping_price(order_no_shipping_discount_ids)

    if order_shipping_discount_ids or order_no_shipping_discount_ids:
        migrate_orders_no_voucher_instance.delay()


def calculate_and_set_undiscounted_base_shipping_price(order_ids):
    orders = Order.objects.filter(id__in=order_ids)
    order_discounts = OrderDiscount.objects.filter(
        order_id__in=orders.values("pk"), type="voucher"
    )
    order_to_discount_amount = {
        order_discount["order_id"]: order_discount["amount"]
        for order_discount in order_discounts.values("order_id", "amount")
    }
    for order in orders:
        order.undiscounted_base_shipping_price_amount = (
            order.base_shipping_price_amount - order_to_discount_amount[order.pk]
        )
    with transaction.atomic():
        _orders = list(orders.select_for_update(of=(["self"])))
        Order.objects.bulk_update(orders, ["undiscounted_base_shipping_price_amount"])
