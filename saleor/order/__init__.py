from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class OrderAppConfig(AppConfig):
    name = 'saleor.order'

    def ready(self):
        from payments.signals import status_changed
        from .signals import order_status_change
        status_changed.connect(order_status_change)


class OrderStatus:
    OPEN = 'open'
    CANCELLED = 'cancelled'
    CLOSED = 'closed'

    CHOICES = [
        (OPEN, pgettext_lazy('order status', 'Open')),
        (CANCELLED, pgettext_lazy('order status', 'Cancelled')),
        (CLOSED, pgettext_lazy('order status', 'Closed'))]
