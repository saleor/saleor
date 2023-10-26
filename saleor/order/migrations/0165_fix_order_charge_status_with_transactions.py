from decimal import Decimal

from babel.numbers import get_currency_precision
from django.db import migrations
from django.db.models.expressions import Exists, OuterRef


def quantize_price(price, currency: str):
    precision = get_currency_precision(currency)
    number_places = Decimal(10) ** -precision
    return price.quantize(number_places)


def update_order_charge_status(order, granted_refund_amount):
    """Update the current charge status for the order.

    We treat the order as overcharged when the charged amount is bigger that
    order.total - order granted refund
    We treat the order as fully charged when the charged amount is equal to
    order.total - order granted refund.
    We treat the order as partially charged when the charged amount covers only part of
    the order.total - order granted refund
    We treat the order as not charged when the charged amount is 0.
    """
    total_charged = order.total_charged_amount or Decimal("0")
    total_charged = quantize_price(total_charged, order.currency)

    current_total_gross = order.total_gross_amount - granted_refund_amount
    current_total_gross = max(current_total_gross, Decimal("0"))
    current_total_gross = quantize_price(current_total_gross, order.currency)

    if total_charged == current_total_gross:
        order.charge_status = "full"
    elif total_charged <= Decimal(0):
        order.charge_status = "none"
    elif total_charged < current_total_gross:
        order.charge_status = "partial"
    else:
        order.charge_status = "overcharged"


def update_orders_charge_statuses_task(Order, OrderGrantedRefund, number=0):
    """Update the charge status for orders with granted refunds.

    Task takes around 0.3 seconds for 1000 orders and around 5 MB of memory.
    """
    batch_size = 1000
    orders = (
        Order.objects.order_by("number")
        .filter(
            Exists(
                OrderGrantedRefund.objects.filter(
                    order_id=OuterRef("pk"),
                )
            ),
            number__gt=number,
        )
        .prefetch_related("granted_refunds")[:batch_size]
    )

    orders_to_update = []
    last_number = number
    for o in orders:
        granted_refund_amount = sum(
            [refund.amount_value for refund in o.granted_refunds.all()], Decimal(0)
        )
        update_order_charge_status(o, granted_refund_amount)
        orders_to_update.append(o)

    if orders_to_update:
        last_number = orders_to_update[-1].number
        Order.objects.bulk_update(orders_to_update, ["charge_status"])

    return last_number, orders_to_update


def update_orders_charge_statuses(apps, schema_editor):
    Order = apps.get_model("order", "Order")
    OrderGrantedRefund = apps.get_model("order", "OrderGrantedRefund")

    number = 0
    while True:
        last_number, orders_to_update = update_orders_charge_statuses_task(
            Order, OrderGrantedRefund, number=number
        )
        number = last_number
        if not orders_to_update:
            break


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0164_auto_20230329_1200"),
    ]
    operations = [
        migrations.RunPython(
            update_orders_charge_statuses, reverse_code=migrations.RunPython.noop
        ),
    ]
