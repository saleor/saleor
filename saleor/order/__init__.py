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
        (DRAFT, pgettext_lazy(
            'Status for a fully editable, not confirmed order created by '
            'staff users',
            'Draft')),
        (UNFULFILLED, pgettext_lazy(
            'Status for an order with any items marked as fulfilled',
            'Unfulfilled')),
        (PARTIALLY_FULFILLED, pgettext_lazy(
            'Status for an order with some items marked as fulfilled',
            'Partially fulfilled')),
        (FULFILLED, pgettext_lazy(
            'Status for an order with all items marked as fulfilled',
            'Fulfilled')),
        (CANCELED, pgettext_lazy(
            'Status for a permanently canceled order',
            'Canceled'))]


class FulfillmentStatus:
    FULFILLED = 'fulfilled'
    CANCELED = 'canceled'

    CHOICES = [
        (FULFILLED, pgettext_lazy(
            'Status for a group of products in an order marked as fulfilled',
            'Fulfilled')),
        (CANCELED, pgettext_lazy(
            'Status for a fulfilled group of products in an order marked '
            'as canceled',
            'Canceled'))]


class CustomPaymentChoices:
    MANUAL = 'manual'

    CHOICES = [
        (MANUAL, pgettext_lazy('Custom payment choice type', 'Manual'))]
