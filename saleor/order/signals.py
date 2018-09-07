import logging

from ..core import analytics
from .emails import send_payment_confirmation
from . import OrderEvents

logger = logging.getLogger(__name__)


def order_status_change(sender, instance, **kwargs):
    """Handle payment status change and set suitable order status."""
    order = instance.order
    if order.is_fully_paid():
        order.history.create(event=OrderEvents.ORDER_FULLY_PAID)
        if order.get_user_current_email():
            send_payment_confirmation.delay(order.pk)
            # TODO send payment confirmation
            order.history.create(
                event=OrderEvents.EMAIL_ORDER_CONFIRMATION_SEND)
        try:
            analytics.report_order(order.tracking_client_id, order)
        except Exception:
            # Analytics failing should not abort the checkout flow
            logger.exception('Recording order in analytics failed')
