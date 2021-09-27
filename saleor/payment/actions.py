from django.core.exceptions import ValidationError

from ..order import events
from ..order.error_codes import OrderErrorCode
from ..payment import gateway
from . import PaymentError


def try_payment_action(order, user, app, payment, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        # provided order might alter it's total_paid.
        order.refresh_from_db()
        return result
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_failed_event(
            order=order, user=user, app=app, message=message, payment=payment
        )
        raise ValidationError(
            {"payment": ValidationError(message, code=OrderErrorCode.PAYMENT_ERROR)}
        )


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
