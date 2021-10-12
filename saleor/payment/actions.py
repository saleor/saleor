from ..order import events
from ..payment import gateway
from . import PaymentError


def try_refund(order, user, app, payment, manager, channel_slug, amount):
    try:
        result = gateway.refund(
            payment,
            manager,
            channel_slug,
            amount,
        )
        return result
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_refund_failed_event(
            order=order, user=user, app=app, message=message, payment=payment
        )
