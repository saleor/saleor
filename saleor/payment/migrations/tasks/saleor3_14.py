from ....celeryconf import app
from ...models import TransactionItem, Payment
from ... import ChargeStatus
from django.db.models import Exists, OuterRef
from django.db import transaction

# Batch size of size 5000 is about 5MB memory usage in task
TRANSACTION_BATCH_SIZE = 5000

# Batch size of size 3000 took about 0.2s and consume about 5MB memory usage
PAYMENT_BATCH_SIZE = 3000


@app.task
def convert_transaction_void_to_cancel_task():
    qs = TransactionItem.objects.filter(available_actions__contains=["void"])
    transaction_ids = qs.values_list("pk", flat=True)[:TRANSACTION_BATCH_SIZE]
    if transaction_ids:
        transactions = TransactionItem.objects.filter(pk__in=transaction_ids)
        for transaction_item in transactions:
            current_available_actions = transaction_item.available_actions
            if "void" in current_available_actions:
                current_available_actions.remove("void")
                if "cancel" not in current_available_actions:
                    current_available_actions.append("cancel")
        TransactionItem.objects.bulk_update(transactions, ["available_actions"])
        convert_transaction_void_to_cancel_task.delay()


@app.task
def fix_invalid_atobarai_payments_task():
    """Fix the invalid payemnts for atobarai gateway.

    Some orders has inactive charged payments and active not charged payments.
    The task will activate the charged payments and deactivate the not charged payments.
    """
    not_charged_active_payments = Payment.objects.filter(
        is_active=True,
        charge_status=ChargeStatus.NOT_CHARGED,
        captured_amount=0,
        gateway="saleor.payments.np-atobarai",
    )
    payments_to_activate_ids = list(
        Payment.objects.filter(
            Exists(not_charged_active_payments.filter(order_id=OuterRef("order_id"))),
            is_active=False,
            charge_status__in=[
                ChargeStatus.FULLY_CHARGED,
                ChargeStatus.PARTIALLY_CHARGED,
            ],
            captured_amount__gt=0,
            gateway="saleor.payments.np-atobarai",
        ).values_list("pk", flat=True)[:PAYMENT_BATCH_SIZE]
    )
    if payments_to_activate_ids:
        payments_to_activate = Payment.objects.filter(pk__in=payments_to_activate_ids)

        related_order_ids = payments_to_activate.values("order_id")
        payments_to_deactivate = Payment.objects.filter(
            order_id__in=related_order_ids, is_active=True
        ).exclude(pk__in=payments_to_activate_ids)

        with transaction.atomic():
            qs = payments_to_deactivate | payments_to_activate
            _payments = list(qs.select_for_update(of=(["self"])))
            payments_to_deactivate.update(is_active=False)
            payments_to_activate.update(is_active=True)

        fix_invalid_atobarai_payments_task.delay()
