from payments.signals import status_changed
from django.dispatch import receiver


@receiver(status_changed)
def order_status_change(sender, instance, **kwargs):
    order = instance.order
    if order.is_full_paid():
        order.change_status('fully-paid')
        instance.send_confirmation_email()
