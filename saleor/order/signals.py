import logging

from django.utils.translation import pgettext_lazy

from ..core import analytics
from .emails import send_order_confirmation

logger = logging.getLogger(__name__)


def order_status_change(sender, instance, **kwargs):
    """Handle payment status change and set suitable order status."""
    order = instance.order
    if order.is_fully_paid():
        order.history.create(
            order=order,
            content=pgettext_lazy(
                'Order status history entry', 'Order fully paid'))
        send_order_confirmation.delay(order.pk)
        try:
            analytics.report_order(order.tracking_client_id, order)
        except Exception:
            # Analytics failing should not abort the checkout flow
            logger.exception('Recording order in analytics failed')
