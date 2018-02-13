import logging

from django.utils.translation import pgettext_lazy

from ..core import analytics
from .emails import  collect_data_for_email, send_order_confirmation

logger = logging.getLogger(__name__)


def order_status_change(sender, instance, **kwargs):
    """Handle payment status change and set suitable order status."""
    order = instance.order
    if order.is_fully_paid():
        order.create_history_entry(
            content=pgettext_lazy(
                'Order status history entry', 'Order fully paid'))
        email_data = collect_data_for_email(order)
        send_order_confirmation.delay(**email_data)
        # instance.send_confirmation_email()
        try:
            analytics.report_order(order.tracking_client_id, order)
        except Exception:
            # Analytics failing should not abort the checkout flow
            logger.exception('Recording order in analytics failed')
