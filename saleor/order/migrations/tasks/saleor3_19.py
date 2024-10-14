from decimal import Decimal

from django.db import transaction
from django.db.models import Exists, F, OuterRef, Q, Sum
from django.forms.models import model_to_dict

from ....account.models import Address
from ....celeryconf import app
from ....discount.models import OrderDiscount, Voucher
from ....warehouse.models import Warehouse
from ...models import Order, OrderLine
from ...utils import update_order_authorize_status, update_order_charge_status

# The batch of size 250 takes ~0.5 second and consumes ~20MB memory at peak
ADDRESS_UPDATE_BATCH_SIZE = 250

# The batch of size 250 takes ~0.2 second and consumes ~20MB memory at peak
ORDER_SET_SHIPPING_PRICE_BATCH_SIZE = 250

# The batch of size 100 takes ~0.2 second and consumes 6.5MB memory
ORDER_SET_SUBTOTAL_PRICE_FOR_ORDER_FROM_BULK = 100


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
    qs = Order.objects.filter(undiscounted_base_shipping_price_amount__isnull=True)
    order_ids = list(
        qs.values_list("pk", flat=True)[:ORDER_SET_SHIPPING_PRICE_BATCH_SIZE]
    )
    if order_ids:
        orders = Order.objects.filter(id__in=order_ids)

        # get orders created from checkout that has shipping discount
        # for draft orders the `base_shipping_price_amount` is the undiscounted price
        # so we can use it as a base for the undiscounted price
        orders_with_shipping_discount = _get_orders_with_shipping_discount(orders)

        orders_no_shipping_discount = orders.exclude(
            Exists(orders_with_shipping_discount.filter(pk=OuterRef("pk")))
        )

        if orders_no_shipping_discount:
            _set_undiscounted_base_shipping_price(orders_no_shipping_discount)
        if orders_with_shipping_discount:
            _calculate_and_set_undiscounted_base_shipping_price(
                orders_with_shipping_discount
            )

        set_udniscounted_base_shipping_price_on_orders_task.delay()


def _get_orders_with_shipping_discount(orders):
    orders_with_shipping_voucher = _get_orders_with_shipping_voucher(orders)
    orders_with_shipping_voucher_no_voucher_instance = (
        _get_orders_with_shipping_voucher_no_voucher_instance(orders)
    )
    return (
        orders_with_shipping_voucher | orders_with_shipping_voucher_no_voucher_instance
    )


def _get_orders_with_shipping_voucher(orders):
    shipping_vouchers = Voucher.objects.filter(type="shipping")
    return orders.filter(
        origin__in=["checkout"],
        voucher_code__isnull=False,
        voucher__isnull=False,
    ).filter(Exists(shipping_vouchers.filter(pk=OuterRef("voucher_id"))))


def _get_orders_with_shipping_voucher_no_voucher_instance(orders):
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

    # order discount must be present for such orders
    order_discounts = OrderDiscount.objects.filter(
        order_id__in=orders.values("pk"), type="voucher"
    )

    # orders with voucher code, no voucher instance, without line vouchers
    # and not applicable order voucher
    return (
        orders.filter(
            origin__in=["checkout"],
            voucher_code__isnull=False,
            voucher__isnull=True,
        )
        .exclude(Exists(lines_with_voucher.filter(order_id=OuterRef("pk"))))
        .filter(
            Exists(lines_with_not_applicable_voucher.filter(order_id=OuterRef("pk")))
        )
        .filter(Exists(order_discounts.filter(order_id=OuterRef("pk"))))
    )


def _calculate_and_set_undiscounted_base_shipping_price(orders):
    order_discounts = OrderDiscount.objects.filter(
        order_id__in=orders.values("pk"), type="voucher"
    )
    order_to_discount_amount = {
        order_discount["order_id"]: order_discount["amount_value"]
        for order_discount in order_discounts.values("order_id", "amount_value")
    }
    for order in orders:
        order.undiscounted_base_shipping_price_amount = (
            order.base_shipping_price_amount
            + order_to_discount_amount.get(order.pk, Decimal("0.0"))
        )
    with transaction.atomic():
        _orders = list(orders.select_for_update(of=(["self"])))
        Order.objects.bulk_update(orders, ["undiscounted_base_shipping_price_amount"])


def _set_undiscounted_base_shipping_price(orders):
    with transaction.atomic():
        _orders = list(orders.select_for_update(of=(["self"])))
        orders.update(
            undiscounted_base_shipping_price_amount=F("base_shipping_price_amount")
        )


def _set_subtotal_for_orders_created_from_bulk(order_ids: list[str]):
    orders = (
        Order.objects.prefetch_related(
            "payments", "payment_transactions", "granted_refunds"
        )
        .filter(id__in=order_ids)
        .annotate(
            sum_line_total_price_net_amount=Sum("lines__total_price_net_amount"),
            sum_line_total_price_gross_amount=Sum("lines__total_price_gross_amount"),
            sum_line_undiscounted_total_price_net_amount=Sum(
                "lines__undiscounted_total_price_net_amount"
            ),
            sum_line_undiscounted_total_price_gross_amount=Sum(
                "lines__undiscounted_total_price_gross_amount"
            ),
            sum_granted_refunds=Sum("granted_refunds__amount_value"),
        )
    )

    for order in orders:
        order.subtotal_net_amount = order.sum_line_total_price_net_amount
        order.subtotal_gross_amount = order.sum_line_total_price_gross_amount
        order.total_net_amount = (
            order.subtotal_net_amount + order.shipping_price_net_amount
        )
        order.total_gross_amount = (
            order.subtotal_gross_amount + order.shipping_price_gross_amount
        )

        # using order.shipping_price as this value is used for storing undiscounted
        # shipping price, received as mutation input or fetched from db.
        order.undiscounted_total_net_amount = (
            order.sum_line_undiscounted_total_price_net_amount
            + order.shipping_price_net_amount
        )
        order.undiscounted_total_gross_amount = (
            order.sum_line_undiscounted_total_price_gross_amount
            + order.shipping_price_gross_amount
        )
        update_order_authorize_status(
            order, granted_refund_amount=order.sum_granted_refunds or Decimal(0)
        )
        update_order_charge_status(
            order, granted_refund_amount=order.sum_granted_refunds or Decimal(0)
        )

    with transaction.atomic():
        _orders = list(
            Order.objects.filter(id__in=order_ids).select_for_update(of=(["self"]))
        )
        Order.objects.bulk_update(
            orders,
            [
                "subtotal_net_amount",
                "subtotal_gross_amount",
                "total_net_amount",
                "total_gross_amount",
                "undiscounted_total_gross_amount",
                "undiscounted_total_net_amount",
                "charge_status",
                "authorize_status",
            ],
        )


@app.task
def set_udniscounted_base_shipping_price_on_draft_orders_task():
    qs = Order.objects.filter(
        undiscounted_base_shipping_price_amount=0,
        base_shipping_price_amount__gt=0,
        status="draft",
    )
    order_ids = list(
        qs.values_list("pk", flat=True)[:ORDER_SET_SHIPPING_PRICE_BATCH_SIZE]
    )
    if order_ids:
        orders = Order.objects.filter(id__in=order_ids)
        _set_undiscounted_base_shipping_price(orders)
        set_udniscounted_base_shipping_price_on_draft_orders_task.delay()


@app.task
def set_order_subtotal_for_orders_created_from_bulk():
    order_lines_qs = OrderLine.objects.filter(total_price_gross_amount__gt=0).values(
        "order_id"
    )
    qs = Order.objects.filter(
        Exists(order_lines_qs.filter(order_id=OuterRef("id"))),
        origin="bulk_create",
        subtotal_gross_amount=Decimal(0),
    )
    order_ids = list(
        qs.values_list("pk", flat=True)[:ORDER_SET_SUBTOTAL_PRICE_FOR_ORDER_FROM_BULK]
    )
    if order_ids:
        _set_subtotal_for_orders_created_from_bulk(order_ids)
        set_order_subtotal_for_orders_created_from_bulk.delay()
