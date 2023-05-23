from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Exists, F, OuterRef

from ....celeryconf import app
from ....order.models import Order, OrderLine
from ....order.tasks import send_order_updated

ORDERS_UPDATE_BATCH_SIZE = 500
SEND_ORDER_UPDATED_BATCH_SIZE = 3500
RAW_0139_UPDATE_SQL = """
    UPDATE "order_orderline"
    SET
        "undiscounted_total_price_gross_amount" = CASE
            WHEN NOT (
                ("order_orderline"."undiscounted_unit_price_gross_amount" * "order_orderline"."quantity") =
                                                    "order_orderline"."undiscounted_total_price_gross_amount")
            THEN ("order_orderline"."undiscounted_unit_price_gross_amount" * "order_orderline"."quantity")
            ELSE "order_orderline"."undiscounted_total_price_gross_amount" END,

        "undiscounted_total_price_net_amount"   = CASE
            WHEN NOT (
                ("order_orderline"."undiscounted_unit_price_net_amount" * "order_orderline"."quantity") =
                                                    "order_orderline"."undiscounted_total_price_net_amount")
            THEN ("order_orderline"."undiscounted_unit_price_net_amount" * "order_orderline"."quantity")
            ELSE "order_orderline"."undiscounted_total_price_net_amount" END

    WHERE (
        NOT ("order_orderline"."undiscounted_total_price_gross_amount" =
                ("order_orderline"."undiscounted_unit_price_gross_amount" *
                "order_orderline"."quantity")) OR
        NOT ("order_orderline"."undiscounted_total_price_net_amount" =
                ("order_orderline"."undiscounted_unit_price_net_amount" *
                "order_orderline"."quantity")))
    RETURNING "order_orderline"."order_id";
"""  # noqa: E501


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:ORDERS_UPDATE_BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


def update_order_undiscounted_price():
    """Fix orders with discount applied on order lines.

    When the order has a voucher discount applied on lines, it is not visible
    on the order's undiscounted total price. This method is fixing such orders.
    """

    # Take orders that has applied lines voucher discounts, but the discount is
    # not visible in undiscounted price.
    orders_to_update = Order.objects.filter(
        Exists(
            OrderLine.objects.filter(
                order_id=OuterRef("id"), voucher_code__isnull=False
            )
        ),
        total_gross_amount=F("undiscounted_total_gross_amount"),
    ).order_by("id")

    updated_orders_pks = []
    for batch_pks in queryset_in_batches(orders_to_update):
        orders = Order.objects.filter(pk__in=batch_pks)
        lines = OrderLine.objects.filter(order_id__in=orders.values("id")).values(
            "order_id",
            "undiscounted_total_price_gross_amount",
            "total_price_gross_amount",
            "undiscounted_total_price_net_amount",
            "total_price_net_amount",
        )
        lines_discount_data = defaultdict(lambda: (0, 0))
        for data in lines:
            discount_amount_gross = (
                data["undiscounted_total_price_gross_amount"]
                - data["total_price_gross_amount"]
            )
            discount_amount_net = (
                data["undiscounted_total_price_net_amount"]
                - data["total_price_net_amount"]
            )
            current_discount_gross, current_discount_net = lines_discount_data[
                data["order_id"]
            ]
            lines_discount_data[data["order_id"]] = (
                current_discount_gross + discount_amount_gross,
                current_discount_net + discount_amount_net,
            )

        for order in orders:
            discount_amount_gross, discount_amount_net = lines_discount_data.get(
                order.id
            )
            if discount_amount_gross > 0 or discount_amount_net > 0:
                order.undiscounted_total_gross_amount += discount_amount_gross
                order.undiscounted_total_net_amount += discount_amount_net

                updated_orders_pks.append(order.id)

        Order.objects.bulk_update(
            orders,
            [
                "undiscounted_total_gross_amount",
                "undiscounted_total_net_amount",
            ],
        )
    return set(updated_orders_pks)


def send_order_updated_events(order_pks):
    list_pks = list(order_pks)

    for index in range(0, len(list_pks), SEND_ORDER_UPDATED_BATCH_SIZE):
        send_order_updated.delay(
            list_pks[index : index + SEND_ORDER_UPDATED_BATCH_SIZE]
        )


@app.task
def fix_undiscounted_prices():
    # 0139_fix_undiscounted_total_on_lines
    with connection.cursor() as cursor:
        cursor.execute(RAW_0139_UPDATE_SQL)
        records = cursor.fetchall()
    updated_orders_pks_from_lines = set(
        [record[0] for record in records] if records else []
    )

    # 0140_fix_order_undiscounted_total
    updated_orders_pks_from_orders = update_order_undiscounted_price()

    # send webhooks for unique order ids
    if all_order_pks := updated_orders_pks_from_lines | updated_orders_pks_from_orders:
        del updated_orders_pks_from_lines
        del updated_orders_pks_from_orders
        send_order_updated_events(all_order_pks)


class Command(BaseCommand):
    def handle(self, *args, **options):
        fix_undiscounted_prices.delay()
