from functools import wraps

from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import pgettext_lazy, npgettext_lazy

from ..account.utils import store_user_address
from ..checkout import AddressType
from ..core.utils.taxes import (
    ZERO_MONEY, get_tax_rate_by_name, get_taxes_for_address)
from ..dashboard.order.utils import get_voucher_discount_for_order
from ..discount.models import NotApplicable
from ..order import FulfillmentStatus, OrderEvents, OrderStatus
from ..order.models import OrderLine
from ..product.utils import allocate_stock, deallocate_stock, increase_stock
from django_prices.templatetags import prices_i18n


def check_order_status(func):
    """Check if order meets preconditions of payment process.

    Order can not have draft status or be fully paid. Billing address
    must be provided.
    If not, redirect to order details page.
    """
    # pylint: disable=cyclic-import
    from .models import Order

    @wraps(func)
    def decorator(*args, **kwargs):
        token = kwargs.pop('token')
        order = get_object_or_404(Order.objects.confirmed(), token=token)
        if not order.billing_address or order.is_fully_paid():
            return redirect('order:details', token=order.token)
        kwargs['order'] = order
        return func(*args, **kwargs)

    return decorator


def update_voucher_discount(func):
    """Recalculate order discount amount based on order voucher."""

    @wraps(func)
    def decorator(*args, **kwargs):
        if kwargs.pop('update_voucher_discount', True):
            order = args[0]
            try:
                discount_amount = get_voucher_discount_for_order(order)
            except NotApplicable:
                discount_amount = ZERO_MONEY
            order.discount_amount = discount_amount
        return func(*args, **kwargs)

    return decorator


@update_voucher_discount
def recalculate_order(order, **kwargs):
    """Recalculate and assign total price of order.

    Total price is a sum of items in order and order shipping price minus
    discount amount.

    Voucher discount amount is recalculated by default. To avoid this, pass
    update_voucher_discount argument set to False.
    """
    # avoid using prefetched order lines
    lines = [OrderLine.objects.get(pk=line.pk) for line in order]
    prices = [line.get_total() for line in lines]
    total = sum(prices, order.shipping_price)
    # discount amount can't be greater than order total
    order.discount_amount = min(order.discount_amount, total.gross)
    if order.discount_amount:
        total -= order.discount_amount
    order.total = total
    order.save()


def update_order_prices(order, discounts):
    """Update prices in order with given discounts and proper taxes."""
    taxes = get_taxes_for_address(order.shipping_address)

    for line in order:
        if line.variant:
            line.unit_price = line.variant.get_price(discounts, taxes)
            line.tax_rate = get_tax_rate_by_name(
                line.variant.product.tax_rate, taxes)
            line.save()

    if order.shipping_method:
        order.shipping_price = order.shipping_method.get_total_price(taxes)
        order.save()

    recalculate_order(order)


def cancel_order(order, restock):
    """Cancel order and associated fulfillments.

    Return products to corresponding stocks if restock is set to True.
    """
    if restock:
        restock_order_lines(order)
    for fulfillment in order.fulfillments.all():
        fulfillment.status = FulfillmentStatus.CANCELED
        fulfillment.save(update_fields=['status'])
    order.status = OrderStatus.CANCELED
    order.save(update_fields=['status'])


def update_order_status(order):
    """Update order status depending on fulfillments."""
    quantity_fulfilled = order.quantity_fulfilled
    total_quantity = order.get_total_quantity()

    if quantity_fulfilled <= 0:
        status = OrderStatus.UNFULFILLED
    elif quantity_fulfilled < total_quantity:
        status = OrderStatus.PARTIALLY_FULFILLED
    else:
        status = OrderStatus.FULFILLED

    if status != order.status:
        order.status = status
        order.save(update_fields=['status'])


def cancel_fulfillment(fulfillment, restock):
    """Cancel fulfillment.

    Return products to corresponding stocks if restock is set to True.
    """
    if restock:
        restock_fulfillment_lines(fulfillment)
    for line in fulfillment:
        order_line = line.order_line
        order_line.quantity_fulfilled -= line.quantity
        order_line.save(update_fields=['quantity_fulfilled'])
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save(update_fields=['status'])
    update_order_status(fulfillment.order)


def attach_order_to_user(order, user):
    """Associate existing order with user account."""
    order.user = user
    store_user_address(user, order.billing_address, AddressType.BILLING)
    if order.shipping_address:
        store_user_address(user, order.shipping_address, AddressType.SHIPPING)
    order.save(update_fields=['user'])


def add_variant_to_order(order, variant, quantity, discounts=None, taxes=None):
    """Add total_quantity of variant to order.

    Raises InsufficientStock exception if quantity could not be fulfilled.
    """
    variant.check_quantity(quantity)

    try:
        line = order.lines.get(variant=variant)
        line.quantity += quantity
        line.save(update_fields=['quantity'])
    except OrderLine.DoesNotExist:
        product_name = variant.display_product()
        translated_product_name = variant.display_product(translated=True)
        if translated_product_name == product_name:
            translated_product_name = ''
        order.lines.create(
            product_name=product_name,
            translated_product_name=translated_product_name,
            product_sku=variant.sku,
            is_shipping_required=variant.is_shipping_required(),
            quantity=quantity,
            variant=variant,
            unit_price=variant.get_price(discounts, taxes),
            tax_rate=get_tax_rate_by_name(variant.product.tax_rate, taxes))

    if variant.track_inventory:
        allocate_stock(variant, quantity)


def change_order_line_quantity(line, new_quantity):
    """Change the quantity of ordered items in a order line."""
    if new_quantity:
        line.quantity = new_quantity
        line.save(update_fields=['quantity'])
    else:
        line.delete()


def restock_order_lines(order):
    """Return ordered products to corresponding stocks."""
    for line in order:
        if line.variant and line.variant.track_inventory:
            if line.quantity_unfulfilled > 0:
                deallocate_stock(line.variant, line.quantity_unfulfilled)
            if line.quantity_fulfilled > 0:
                increase_stock(line.variant, line.quantity_fulfilled)

        if line.quantity_fulfilled > 0:
            line.quantity_fulfilled = 0
            line.save(update_fields=['quantity_fulfilled'])


def restock_fulfillment_lines(fulfillment):
    """Return fulfilled products to corresponding stocks."""
    for line in fulfillment:
        if line.order_line.variant and line.order_line.variant.track_inventory:
            increase_stock(
                line.order_line.variant, line.quantity, allocate=True)


def display_order_event(event_type, params):
    """This function is to keep backwards compatibility with the old dashboard
    and new type of order events (storing enums instead of messages)
    """
    if event_type == OrderEvents.ORDER_DRAFT_PLACED:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order created from draft order')
    if event_type == OrderEvents.EMAIL_ORDER_CONFIRMATION_SEND:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order confirmation email was sent to user'
            '(%(email)s)') % {'email': params['email']}
    if event_type == OrderEvents.PAYMENT_RELEASED:
        return pgettext_lazy(
            'Dashboard message related to an order', 'Released payment')
    if event_type == OrderEvents.PAYMENT_REFUNDED:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Refunded %(amount)s' % {
                'amount': prices_i18n.amount(params['amount'])})
    if event_type == OrderEvents.PAYMENT_CAPTURED:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Captured %(amount)s' % {
                'amount': prices_i18n.amount(params['amount'])})
    if event_type == OrderEvents.ORDER_MARKED_AS_PAID:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Order manually marked as paid.')
    if event_type == OrderEvents.ORDER_CANCELED:
        return pgettext_lazy(
            'Dashboard message related to an order', 'Order canceled')
    if event_type == OrderEvents.FULFILLMENT_RESTOCKED_ITEMS:
        return npgettext_lazy(
            'Dashboard message related to an order',
            'Restocked %(quantity)d item',
            'Restocked %(quantity)d items',
            'quantity') % {'quantity': params['quantity']}
    if event_type == OrderEvents.NOTE_ADDED:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Added note: %(note)s' % {'note': params['message']})
    if event_type == OrderEvents.FULFILLMENT_CANCELED:
        return pgettext_lazy(
            'Dashboard message',
            'Fulfillment #%(fulfillment)s canceled') % {
                'fulfillment': params['id']}
    if event_type == OrderEvents.FULFILLMENT_FULFILLED_ITEMS:
        return npgettext_lazy(
            'Dashboard message related to an order',
            'Fulfilled %(quantity_fulfilled)d item',
            'Fulfilled %(quantity_fulfilled)d items',
            'quantity_fulfilled') % {
                'quantity_fulfilled': params['quantity']}
    if event_type == OrderEvents.EMAIL_SHIPPING_CONFIRMATION_SEND:
        return pgettext_lazy(
            'Dashboard message related to an order',
            'Shipping confirmation email was sent to user'
            '(%(email)s)') % {'email': params['email']}
