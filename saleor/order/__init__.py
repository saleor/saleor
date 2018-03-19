from django.apps import AppConfig
from django.utils.translation import pgettext_lazy


class OrderAppConfig(AppConfig):
    name = 'saleor.order'

    def ready(self):
        from payments.signals import status_changed
        from .signals import order_status_change
        status_changed.connect(order_status_change)


class OrderStatus:
    DRAFT = 'draft'
    UNFULFILLED = 'unfulfilled'
    PARTIALLY_FULFILLED = 'partially fulfilled'
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'

    CHOICES = [
        (DRAFT, pgettext_lazy('order status', 'Draft')),
        (UNFULFILLED, pgettext_lazy('order status', 'Unfulfilled')),
        (PARTIALLY_FULFILLED, pgettext_lazy(
            'order status', 'Partially fulfilled')),
        (FULFILLED, pgettext_lazy('order status', 'Fulfilled')),
        (CANCELED, pgettext_lazy('order status', 'Canceled'))]


class FulfillmentStatus:
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'

    CHOICES = [
        (FULFILLED, pgettext_lazy('order status', 'Fulfilled')),
        (CANCELED, pgettext_lazy('order status', 'Canceled'))]
