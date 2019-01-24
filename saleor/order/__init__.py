from enum import Enum

from django.conf import settings
from django.utils.translation import npgettext_lazy, pgettext_lazy
from django_prices.templatetags import prices_i18n
from prices import Money


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
            'Status for an order with no items marked as fulfilled',
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


class OrderEvents(Enum):
    PLACED = 'placed'
    PLACED_FROM_DRAFT = 'draft_placed'
    OVERSOLD_ITEMS = 'oversold_items'
    ORDER_MARKED_AS_PAID = 'marked_as_paid'
    CANCELED = 'canceled'
    ORDER_FULLY_PAID = 'order_paid'
    UPDATED = 'updated'

    EMAIL_SENT = 'email_sent'

    PAYMENT_CAPTURED = 'captured'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_VOIDED = 'voided'

    FULFILLMENT_CANCELED = 'fulfillment_canceled'
    FULFILLMENT_RESTOCKED_ITEMS = 'restocked_items'
    FULFILLMENT_FULFILLED_ITEMS = 'fulfilled_items'
    TRACKING_UPDATED = 'tracking_updated'
    NOTE_ADDED = 'note_added'

    # Used mostly for importing legacy data from before Enum-based events
    OTHER = 'other'


class OrderEventsEmails(Enum):
    PAYMENT = 'payment_confirmation'
    SHIPPING = 'shipping_confirmation'
    ORDER = 'order_confirmation'
    FULFILLMENT = 'fulfillment_confirmation'


EMAIL_CHOICES = {
    OrderEventsEmails.PAYMENT.value: pgettext_lazy(
        'Email type', 'Payment confirmation'),
    OrderEventsEmails.SHIPPING.value: pgettext_lazy(
        'Email type', 'Shipping confirmation'),
    OrderEventsEmails.FULFILLMENT.value: pgettext_lazy(
        'Email type', 'Fulfillment confirmation'),
    OrderEventsEmails.ORDER.value: pgettext_lazy(
        'Email type', 'Order confirmation')}


def get_money_from_params(amount):
    """Money serialization changed at one point, as for now it's serialized
    as a dict. But we keep those settings for the legacy data.

    Can be safely removed after migrating to Dashboard 2.0
    """
    if isinstance(amount, Money):
        return amount
    if isinstance(amount, dict):
        return Money(amount=amount['amount'], currency=amount['currency'])
    return Money(amount, settings.DEFAULT_CURRENCY)


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
    if event_type == OrderEvents.PAYMENT_VOIDED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Payment was voided by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.PAYMENT_REFUNDED.value:
        amount = get_money_from_params(params['amount'])
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Successfully refunded: %(amount)s' % {
                'amount': prices_i18n.amount(amount)})
    if event_type == OrderEvents.PAYMENT_CAPTURED.value:
        amount = get_money_from_params(params['amount'])
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Successfully captured: %(amount)s' % {
                'amount': prices_i18n.amount(amount)})
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
            number='quantity') % {'quantity': params['quantity']}
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
                'fulfillment': params['composed_id'],
                'user_name': order_event.user}
    if event_type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS.value:
        return npgettext_lazy(
            'Dashboard message related to an order',
            'Fulfilled %(quantity_fulfilled)d item',
            'Fulfilled %(quantity_fulfilled)d items',
            number='quantity_fulfilled') % {
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
                'email_type': EMAIL_CHOICES[params['email_type']],
                'email': params['email']}
    if event_type == OrderEvents.UPDATED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order details were updated by %(user_name)s' % {
                'user_name': order_event.user})
    if event_type == OrderEvents.TRACKING_UPDATED.value:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Fulfillment #%(fulfillment)s tracking was updated to'
            ' %(tracking_number)s by %(user_name)s') % {
                'fulfillment': params['composed_id'],
                'tracking_number': params['tracking_number'],
                'user_name': order_event.user}
    if event_type == OrderEvents.OVERSOLD_ITEMS.value:
        return npgettext_lazy(
            'Dashboard message related to an order',
            '%(quantity)d line item oversold on this order.',
            '%(quantity)d line items oversold on this order.',
            number='quantity') % {
                'quantity': len(params['oversold_items'])}

    if event_type == OrderEvents.OTHER.value:
        return order_event.parameters['message']
    raise ValueError('Not supported event type: %s' % (event_type))
