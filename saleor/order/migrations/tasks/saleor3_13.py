from decimal import Decimal

from django.db.models import DecimalField, Sum
from django.db.models.expressions import Exists, F, OuterRef
from django.db.models.functions import Coalesce

from ....celeryconf import app
from ... import OrderChargeStatus
from ...models import Order, OrderGrantedRefund

# Batch size of size 5000 is about 3MB memory usage in task
BATCH_SIZE = 5000


@app.task
def update_orders_charge_statuses_task():
    orders = Order.objects.filter(
        Exists(OrderGrantedRefund.objects.filter(order_id=OuterRef("pk")))
    )
    orders = orders.annotate(
        refunded_amount=Coalesce(
            Sum("granted_refunds__amount_value"),
            0,
            output_field=DecimalField(),
        ),
        current_total_gross=F("total_gross_amount") - F("refunded_amount"),
    )
    trigger_task = False

    overcharged_orders = orders.filter(
        total_charged_amount__gt=F("current_total_gross")
    ).exclude(charge_status=OrderChargeStatus.OVERCHARGED)[:BATCH_SIZE]
    if overcharged_orders.exists():
        order_pks = overcharged_orders.values_list("pk", flat=True)
        Order.objects.filter(id__in=order_pks).update(
            charge_status=OrderChargeStatus.OVERCHARGED
        )
        trigger_task = True

    full_orders = orders.filter(total_charged_amount=F("current_total_gross")).exclude(
        charge_status=OrderChargeStatus.FULL
    )[:BATCH_SIZE]
    if full_orders.exists():
        order_pks = full_orders.values_list("pk", flat=True)
        Order.objects.filter(id__in=order_pks).update(
            charge_status=OrderChargeStatus.FULL
        )
        trigger_task = True

    partial_orders = orders.filter(
        total_charged_amount__lt=F("current_total_gross"),
        total_charged_amount__gt=Decimal(0),
    ).exclude(charge_status=OrderChargeStatus.PARTIAL)[:BATCH_SIZE]
    if partial_orders.exists():
        order_pks = partial_orders.values_list("pk", flat=True)
        Order.objects.filter(id__in=order_pks).update(
            charge_status=OrderChargeStatus.PARTIAL
        )
        trigger_task = True

    none_orders = orders.filter(
        total_charged_amount__lte=Decimal(0), current_total_gross__gt=Decimal(0)
    ).exclude(charge_status=OrderChargeStatus.NONE)[:BATCH_SIZE]
    if none_orders.exists():
        order_pks = none_orders.values_list("pk", flat=True)
        Order.objects.filter(id__in=order_pks).update(
            charge_status=OrderChargeStatus.NONE
        )
        trigger_task = True

    if trigger_task:
        update_orders_charge_statuses_task.delay()
