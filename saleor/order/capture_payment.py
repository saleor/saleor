from decimal import Decimal

from saleor.order.models import Order
from saleor.order.utils import get_active_payments
from saleor.payment import gateway
from saleor.payment.models import Payment
from saleor.plugins.manager import PluginsManager


def capture_payment(
    order: Order, payment: Payment, manager: PluginsManager, to_pay: Decimal
):
    if payment and payment.can_capture():
        amount = min(to_pay, payment.get_charge_amount())
        gateway.capture(
            payment,
            manager,
            channel_slug=order.channel.slug,
            amount=amount,
        )
        return amount

    return Decimal("0.0")


def capture_payments(order: Order, manager: PluginsManager):
    # order.status = OrderStatus.UNFULFILLED
    # order.save(update_fields=["status"])
    to_pay = order.missing_amount_to_be_paid().amount
    payments_to_notify = []
    for payment in get_active_payments(order):  # move it to dedicated file
        if to_pay > Decimal("0.00"):
            to_pay -= capture_payment(order, payment, manager, to_pay)
            payments_to_notify.append(dict(amount=payment.total, payment=payment))
        else:
            break

    return payments_to_notify
