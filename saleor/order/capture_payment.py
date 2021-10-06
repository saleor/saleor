from decimal import Decimal
from typing import Optional

from saleor.account.models import User
from saleor.app.models import App
from saleor.order import events
from saleor.order.interface import OrderPaymentAction
from saleor.order.models import Order
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
) -> Optional[Transaction]:
    if payment and payment.can_capture():
        amount = min(to_pay, payment.get_charge_amount())
        try:
            return gateway.capture(
                payment,
                manager,
                channel_slug=order.channel.slug,
                amount=amount,
            )
        except PaymentError as e:
            events.payment_capture_failed_event(
                order=order, user=user, app=app, message=str(e), payment=payment
            )

    return None


def capture_payments(
    order: Order,
    manager: PluginsManager,
    user: Optional[User],
    app: Optional[App],
    amount: Decimal = None,
):
    to_pay = amount or order.outstanding_balance.amount
    payments_to_notify = []

    # We iterate over payments in the order in which they were created
    authorized_payments = sorted(
        [p for p in get_active_payments(order) if p.is_authorized],
        key=lambda p: p.pk,
    )
    for payment in authorized_payments:
        if to_pay > Decimal("0.00"):
            transaction = _capture_payment(order, payment, manager, user, app, to_pay)
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

        else:
            break

    return payments_to_notify
