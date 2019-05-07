from functools import wraps

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from prices import Money, TaxedMoney

from ..account.utils import store_user_address
from ..checkout import AddressType
from ..core.utils.taxes import (
    ZERO_MONEY, get_tax_rate_by_name, get_taxes_for_address)
from ..core.weight import zero_weight
from ..dashboard.order.utils import get_voucher_discount_for_order
from ..discount.models import NotApplicable
from ..order import FulfillmentStatus, OrderStatus, emails
from ..order.models import Fulfillment, FulfillmentLine, Order, OrderLine
from ..payment import ChargeStatus
from ..payment.utils import gateway_refund, gateway_void
from ..product.utils import (
    allocate_stock, deallocate_stock, decrease_stock, increase_stock)
from ..product.utils.digital_products import (
    get_default_digital_content_settings)


def order_line_needs_automatic_fulfillment(line: OrderLine) -> bool:
    """Check if given line is digital and should be automatically fulfilled"""
    digital_content_settings = get_default_digital_content_settings()
    default_automatic_fulfillment = (
        digital_content_settings['automatic_fulfillment'])
    content = line.variant.digital_content
    if default_automatic_fulfillment and content.use_default_settings:
        return True
    if content.automatic_fulfillment:
        return True
    return False


def order_needs_automatic_fullfilment(order: Order) -> bool:
    """Check if order has digital products which should be automatically
    fulfilled"""
    for line in order.lines.digital():
        if order_line_needs_automatic_fulfillment(line):
            return True
    return False


def fulfill_order_line(order_line, quantity):
    """Fulfill order line with given quantity."""
    if order_line.variant and order_line.variant.track_inventory:
        decrease_stock(order_line.variant, quantity)
    order_line.quantity_fulfilled += quantity
    order_line.save(update_fields=['quantity_fulfilled'])


def automatically_fulfill_digital_lines(order: Order):
    """Fulfill all digital lines which have enabled automatic fulfillment
    setting and send confirmation email."""
    digital_lines = order.lines.filter(
        is_shipping_required=False, variant__digital_content__isnull=False)
    digital_lines = digital_lines.prefetch_related('variant__digital_content')

    if not digital_lines:
        return
    fulfillment, _ = Fulfillment.objects.get_or_create(order=order)
    for line in digital_lines:
        if not order_line_needs_automatic_fulfillment(line):
            continue
        digital_content = line.variant.digital_content
        digital_content.urls.create(line=line)
        quantity = line.quantity
        FulfillmentLine.objects.create(
            fulfillment=fulfillment, order_line=line,
            quantity=quantity)
        fulfill_order_line(order_line=line, quantity=quantity)
    emails.send_fulfillment_confirmation.delay(order.pk, fulfillment.pk)


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
    recalculate_order_weight(order)


def recalculate_order_weight(order):
    """Recalculate order weights."""
    weight = zero_weight()
    for line in order:
        if line.variant:
            weight += line.variant.get_weight() * line.quantity
    order.weight = weight
    order.save(update_fields=['weight'])


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
        order.shipping_price = order.shipping_method.get_total(taxes)
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

    payments = order.payments.filter(is_active=True).exclude(
        charge_status=ChargeStatus.FULLY_REFUNDED)

    for payment in payments:
        if payment.can_refund():
            gateway_refund(payment)
        elif payment.can_void():
            gateway_void(payment)


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


@transaction.atomic
def add_variant_to_order(
        order,
        variant,
        quantity,
        discounts=None,
        taxes=None,
        allow_overselling=False,
        track_inventory=True):
    """Add total_quantity of variant to order.

    Returns an order line the variant was added to.

    By default, raises InsufficientStock exception if  quantity could not be
    fulfilled. This can be disabled by setting `allow_overselling` to True.
    """
    if not allow_overselling:
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
        line = order.lines.create(
            product_name=product_name,
            translated_product_name=translated_product_name,
            product_sku=variant.sku,
            is_shipping_required=variant.is_shipping_required(),
            quantity=quantity,
            variant=variant,
            unit_price=variant.get_price(discounts, taxes),
            tax_rate=get_tax_rate_by_name(variant.product.tax_rate, taxes))

    if variant.track_inventory and track_inventory:
        allocate_stock(variant, quantity)
    return line


def change_order_line_quantity(line, new_quantity):
    """Change the quantity of ordered items in a order line."""
    if new_quantity:
        line.quantity = new_quantity
        line.save(update_fields=['quantity'])
    else:
        delete_order_line(line)


def delete_order_line(line):
    """Delete an order line from an order."""
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


def sum_order_totals(qs):
    zero = Money(0, currency=settings.DEFAULT_CURRENCY)
    taxed_zero = TaxedMoney(zero, zero)
    return sum([order.total for order in qs], taxed_zero)
