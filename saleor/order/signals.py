import logging
from django.dispatch import receiver
from payments.signals import status_changed

from ..core import analytics

logger = logging.getLogger(__name__)


@receiver(status_changed)
def order_status_change(sender, instance, **kwargs):
    """Handles payment status change and sets suitable order status."""
    order = instance.order
    if order.is_fully_paid():
        order.create_history_entry(
            status=order.status, comment=pgettext_lazy(
                'Order status history entry', 'Order fully paid'))
        instance.send_confirmation_email()
        try:
            analytics.report_order(order.tracking_client_id, order)
        except Exception:
            # Analytics failing should not abort the checkout flow
            logger.exception('Recording order in analytics failed')
