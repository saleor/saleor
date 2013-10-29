from payments.signals import status_changed
from django.dispatch import receiver

from ..core import analytics


@receiver(status_changed)
def order_status_change(sender, instance, **kwargs):
    order = instance.order
    if order.is_fully_paid():
        order.change_status('fully-paid')
        instance.send_confirmation_email()
        analytics.report_order(order.tracking_client_id, order)
