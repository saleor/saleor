from functools import wraps

from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect
from prices import Money

from ..account.utils import store_user_address
from ..core.exceptions import InsufficientStock
from ..core.utils import DEFAULT_TAX_RATE_NAME
from ..dashboard.order.utils import get_voucher_discount_for_order
from ..order import FulfillmentStatus, OrderStatus
from ..order.models import OrderLine
from ..product.utils import allocate_stock, deallocate_stock, increase_stock


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
            order.discount_amount = (
                get_voucher_discount_for_order(order) or
                Money(0, settings.DEFAULT_CURRENCY))
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
    """Associates existing order with user account."""
    order.user = user
    store_user_address(user, order.billing_address, billing=True)
    if order.shipping_address:
        store_user_address(user, order.shipping_address, shipping=True)
    order.save(update_fields=['user'])


def get_variant_tax_rate(variant, taxes=None):
    """Return value of variant tax rate for current taxes."""
    if not taxes:
        return 0

    rate_name = variant.product.tax_rate
    if rate_name in taxes:
        tax = taxes[rate_name]
    else:
        tax = taxes[DEFAULT_TAX_RATE_NAME]

    return tax['value']


def add_variant_to_order(
        order, variant, total_quantity, discounts=None, taxes=None,
        add_to_existing=True):
    """Add total_quantity of variant to order.

    Raises InsufficientStock exception if quantity could not be fulfilled.

    By default, first adds variant to existing lines with same variant.
    It can be disabled with setting add_to_existing to False.

    Order lines are created by increasing quantity of lines,
    as long as total_quantity of variant will be added.
    """
    quantity_not_fulfilled = add_variant_to_existing_lines(
        order, variant, total_quantity) if add_to_existing else total_quantity
    if not quantity_not_fulfilled:
        return
    if quantity_not_fulfilled > variant.quantity_available:
        raise InsufficientStock(variant)
    price = variant.get_price(discounts, taxes=taxes)
    order.lines.create(
        product_name=variant.display_product(),
        product_sku=variant.sku,
        is_shipping_required=(
            variant.product.product_type.is_shipping_required),
        quantity=quantity_not_fulfilled,
        unit_price=price,
        variant=variant,
        tax_rate=get_variant_tax_rate(variant, taxes))
    allocate_stock(variant, quantity_not_fulfilled)


def add_variant_to_existing_lines(order, variant, total_quantity):
    """Add variant to existing lines with same variant.

    Variant is added by increasing quantity of lines with same variant,
    as long as total_quantity of variant will be added
    or there is no more lines with same variant.

    Returns quantity that could not be fulfilled with existing lines.
    """
    # order descending by lines' stock available quantity
    lines = order.lines.filter(variant=variant).order_by(
        F('variant__quantity_allocated') - F('variant__quantity'))

    quantity_left = total_quantity
    for line in lines:
        quantity = (
            line.variant.quantity_available
            if quantity_left > line.variant.quantity_available
            else quantity_left)
        line.quantity += quantity
        line.save()
        allocate_stock(line.variant, quantity)
        quantity_left -= quantity
        if quantity_left == 0:
            break
    return quantity_left


def merge_duplicates_into_order_line(line):
    """Merge duplicated lines in order into one (given) line.

    If there are no duplicates, nothing will happen.
    """
    lines = line.order.lines.filter(
        product_name=line.product_name, product_sku=line.product_sku,
        variant=line.variant, is_shipping_required=line.is_shipping_required)
    if lines.count() > 1:
        line.quantity = sum([line.quantity for line in lines])
        line.save(update_fields=['quantity'])
        lines.exclude(pk=line.pk).delete()


def change_order_line_quantity(line, new_quantity):
    """Change the quantity of ordered items in a order line."""
    if new_quantity:
        line.quantity = new_quantity
        line.save()
    else:
        line.delete()


def restock_order_lines(order):
    """Return ordered products to corresponding stocks."""
    for line in order:
        if line.variant:
            if line.quantity_unfulfilled > 0:
                deallocate_stock(line.variant, line.quantity_unfulfilled)
            if line.quantity_fulfilled > 0:
                increase_stock(line.variant, line.quantity_fulfilled)
                line.quantity_fulfilled = 0
                line.save(update_fields=['quantity_fulfilled'])


def restock_fulfillment_lines(fulfillment, allocate=True):
    """Return fulfilled products to corresponding stocks."""
    for line in fulfillment:
        order_line = line.order_line
        if order_line.variant:
            increase_stock(
                line.order_line.variant, line.quantity, allocate=allocate)
