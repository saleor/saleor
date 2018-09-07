from django.apps import AppConfig
from django.utils.translation import pgettext_lazy
from enum import Enum


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


class OrderEvents(Enum):
    ORDER_PLACED = 'placed'
    ORDER_DRAFT_PLACED = 'draft_placed'
    ORDER_MARKED_AS_PAID = 'marked_as_paid'
    ORDER_CANCELED = 'canceled'
    ORDER_FULLY_PAID = 'order_paid'
    ORDER_UPDATED = 'order_updated'

    EMAIL_ORDER_CONFIRMATION_SEND = 'order_confirmation_mail_send'
    EMAIL_SHIPPING_CONFIRMATION_SEND = 'shipping_confirmation_mail_send'

    PAYMENT_CAPTURED = 'captured'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_RELEASED = 'released'

    FULFILLMENT_CANCELED = 'fulfillment_canceled'
    FULFILLMENT_RESTOCKED_ITEMS = 'restocked_items'
    FULFILLMENT_FULFILLED_ITEMS = 'fulfilled_items'

    NOTE_ADDED = 'note_added'
