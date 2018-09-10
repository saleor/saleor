from enum import Enum

from django.apps import AppConfig
from django.utils.translation import pgettext_lazy, npgettext_lazy
from django_prices.templatetags import prices_i18n


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
    PLACED = 'placed'
    PLACED_FROM_DRAFT = 'draft_placed'
    ORDER_MARKED_AS_PAID = 'marked_as_paid'
    CANCELED = 'canceled'
    ORDER_FULLY_PAID = 'order_paid'
    UPDATED = 'updated'

    EMAIL_SENT = 'email_sent'

    PAYMENT_CAPTURED = 'captured'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_RELEASED = 'released'

    FULFILLMENT_CANCELED = 'fulfillment_canceled'
    FULFILLMENT_RESTOCKED_ITEMS = 'restocked_items'
    FULFILLMENT_FULFILLED_ITEMS = 'fulfilled_items'

    NOTE_ADDED = 'note_added'


class OrderEventsEmail:
    PAYMENT = 'payment_confirmation'
    SHIPPING = 'shipping_confirmation'
    ORDER = 'order_confirmation'

    CHOICES = {
        PAYMENT: pgettext_lazy('Email type', 'Payment confirmation'),
        SHIPPING: pgettext_lazy('Email type', 'Shipping confirmation'),
        ORDER: pgettext_lazy('Email type', 'Order confirmation')}


def display_order_event(order_event):
    """This function is used to keep the  backwards compatibility
    with the old dashboard and new type of order events
    (storing enums instead of messages)
    """
    event_type = order_event.type
    params = order_event.parameters
    if event_type == OrderEvents.PLACED_FROM_DRAFT.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order created from draft order by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.PAYMENT_RELEASED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Payment was released by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.PAYMENT_REFUNDED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Successfully refunded: %(amount)s' % {
                'amount': prices_i18n.amount(params['amount'])})
    if event_type == OrderEvents.PAYMENT_CAPTURED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Successfully captured: %(amount)s' % {
                'amount': prices_i18n.amount(params['amount'])})
    if event_type == OrderEvents.ORDER_MARKED_AS_PAID.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order manually marked as paid by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.CANCELED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order was canceled by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value:
        return npgettext_lazy(
            'Dashboard message related to an order',
            'We restocked %(quantity)d item',
            'We restocked %(quantity)d items',
            'quantity') % {'quantity': params['quantity']}
    if event_type == OrderEvents.NOTE_ADDED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            '%(user_name)s added note: %(note)s' % {
                'note': params['message'],
                'user_name': order_event.user})
    if event_type == OrderEvents.FULFILLMENT_CANCELED.value:
        return pgettext_lazy(
            'Dashboard message',
            'Fulfillment #%(fulfillment)s canceled by %(user_name)s') % {
                'fulfillment': params['id'],
                'user_name': order_event.user}
    if event_type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value:
        return npgettext_lazy(
            'Dashboard message related to an order',
            'Fulfilled %(quantity_fulfilled)d item',
            'Fulfilled %(quantity_fulfilled)d items',
            'quantity_fulfilled') % {
                'quantity_fulfilled': params['quantity']}
    if event_type == OrderEvents.PLACED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order was placed')
    if event_type == OrderEvents.ORDER_FULLY_PAID.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order was fully paid')
    if event_type == OrderEvents.EMAIL_SENT.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            '%(email_type)s email was sent to the customer '
            '(%(email)s)') % {
                'email_type': OrderEventsEmail.CHOICES[params['email_type']],
                'email': params['email']}
    if event_type == OrderEvents.UPDATED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order details were updated by %(user_name)s' % {
                'user_name': order_event.user})
    raise ValueError('Not supported event type: %s' % (event_type))
