from decimal import Decimal
from typing import Optional, Tuple

from saleor.account.models import User
from saleor.app.models import App
from saleor.order import events
from saleor.order.interface import OrderPaymentAction
from saleor.order.models import Order, OrderEvent
from saleor.order.utils import get_active_payments
from saleor.payment import PaymentError, TransactionKind, gateway
from saleor.payment.models import Payment, Transaction
from saleor.plugins.manager import PluginsManager


def _capture_payment(
    order: Order,
    payment: Payment,
    manager: PluginsManager,
    user: Optional[User],
    app: Optional["App"],
    to_pay: Decimal,
) -> Tuple[Optional[Transaction], Optional[OrderEvent]]:
    if payment and payment.can_capture():
        amount = min(to_pay, payment.get_charge_amount())
        try:
            return (
                gateway.capture(
                    payment,
                    manager,
                    channel_slug=order.channel.slug,
                    amount=amount,
                ),
                None,
            )
        except PaymentError as e:
            return None, events.payment_capture_failed_event(
                order=order, user=user, app=app, message=str(e), payment=payment
            )

    return None, None


def capture_payments(
    order: Order,
    manager: PluginsManager,
    user: Optional[User],
    app: Optional[App],
    amount: Decimal = None,
):
    to_pay = amount or order.missing_amount_to_be_paid().amount
    payments_to_notify = []
    failed_events = []

    # We iterate over payments in the order in which they were created
    authorized_payments = sorted(
        [p for p in get_active_payments(order) if p.is_authorized],
        key=lambda p: p.pk,
    )
    for payment in authorized_payments:
        if to_pay > Decimal("0.00"):
            transaction, event = _capture_payment(
                order, payment, manager, user, app, to_pay
            )
            # Process only successful charges
            if transaction and transaction.is_success:
                to_pay -= transaction.amount
                #  Confirm that we changed the status to capture. Some payments
                #  can receive asynchronous webhooks with status updates
                if transaction.kind == TransactionKind.CAPTURE:
                    payments_to_notify.append(
                        OrderPaymentAction(
                            amount=transaction.amount,
                            payment=payment,
                        )
                    )
            elif event:
                failed_events.append(event)

        else:
            break

    return payments_to_notify, failed_events


def _void_payment(
    order: Order,
    payment: Payment,
    manager: PluginsManager,
    user: Optional[User],
    app: Optional["App"],
) -> Tuple[Optional[Transaction], Optional[OrderEvent]]:
    if payment and payment.can_void():
        try:
            return (
                gateway.void(
                    payment,
                    manager,
                    channel_slug=order.channel.slug,
                ),
                None,
            )
        except PaymentError as e:
            return None, events.payment_void_failed_event(
                order=order, user=user, app=app, message=str(e), payment=payment
            )

    return None, None


def void_payments(
    order: Order,
    manager: PluginsManager,
    user: Optional[User],
    app: Optional[App],
):
    payments_to_notify = []
    failed_events = []

    # We iterate over payments in the order in which they were created
    authorized_payments = sorted(
        [p for p in get_active_payments(order) if p.is_authorized],
        key=lambda p: p.pk,
    )
    for payment in authorized_payments:
        transaction, event = _void_payment(order, payment, manager, user, app)
        # Process only successful voids
        if transaction and transaction.is_success:
            #  Confirm that we changed the status to VOID. Some payments
            #  can receive asynchronous webhooks with status updates
            if transaction.kind == TransactionKind.VOID:
                payments_to_notify.append(
                    OrderPaymentAction(
                        amount=transaction.amount,
                        payment=payment,
                    )
                )
        elif event:
            failed_events.append(event)

    return payments_to_notify, failed_events
