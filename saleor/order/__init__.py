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
    CLOSED = 'closed'

    CHOICES = [
        (OPEN, pgettext_lazy('order status', 'Open')),
        (CLOSED, pgettext_lazy('order status', 'Closed'))]


class GroupStatus:
    NEW = 'new'
    CANCELLED = 'cancelled'
    SHIPPED = 'shipped'

    CHOICES = [
        (NEW, pgettext_lazy('group status', 'Processing')),
        (CANCELLED, pgettext_lazy('group status', 'Cancelled')),
        (SHIPPED, pgettext_lazy('group status', 'Shipped'))]
