from prices import Money

from saleor.order import OrderStatus
from saleor.order.models import Order
from saleor.payment import gateway
from saleor.plugins.manager import PluginsManager


def capture_payment(order, payment, manager, to_pay):
    if payment and payment.can_capture():
        amount = min(to_pay, Money(payment.get_charge_amount(), payment.currency))
        gateway.capture(
            payment,
            manager,
            channel_slug=order.channel.slug,
            amount=amount,
        )
        return amount


def capture_payments(order: Order, manager: PluginsManager):
    order.status = OrderStatus.UNFULFILLED
    order.save(update_fields=["status"])
    to_pay = order.missing_amount_to_be_paid()
    payments_to_notify = []
    for payment in order.get_active_payments():  # move it to dedicated file
        if to_pay > Money(0, to_pay.currency):
            to_pay -= capture_payment(order, payment, manager, to_pay)
            payments_to_notify.append(dict(amount=payment.total, payment=payment))
        else:
            break

    return payments_to_notify
