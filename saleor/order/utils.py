from functools import wraps

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from prices import Money, TaxedMoney

from ..account.utils import store_user_address
from ..checkout import AddressType
from ..core.taxes import zero_money
from ..core.weight import zero_weight
from ..dashboard.order.utils import get_voucher_discount_for_order
from ..discount.models import NotApplicable
from ..extensions.manager import get_extensions_manager
from ..order import OrderStatus
from ..order.models import Order, OrderLine
from ..product.utils import allocate_stock, deallocate_stock, increase_stock
from ..product.utils.digital_products import get_default_digital_content_settings
from ..shipping.models import ShippingMethod
from . import events


def order_line_needs_automatic_fulfillment(line: OrderLine) -> bool:
    """Check if given line is digital and should be automatically fulfilled."""
    digital_content_settings = get_default_digital_content_settings()
    default_automatic_fulfillment = digital_content_settings["automatic_fulfillment"]
    content = line.variant.digital_content
    if default_automatic_fulfillment and content.use_default_settings:
        return True
    if content.automatic_fulfillment:
        return True
    return False


def order_needs_automatic_fullfilment(order: Order) -> bool:
    """Check if order has digital products which should be automatically fulfilled."""
    for line in order.lines.digital():
        if order_line_needs_automatic_fulfillment(line):
            return True
    return False


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
        token = kwargs.pop("token")
        order = get_object_or_404(Order.objects.confirmed(), token=token)
        if not order.billing_address or order.is_fully_paid():
            return redirect("order:details", token=order.token)
        kwargs["order"] = order
        return func(*args, **kwargs)

    return decorator


def update_voucher_discount(func):
    """Recalculate order discount amount based on order voucher."""

    @wraps(func)
    def decorator(*args, **kwargs):
        if kwargs.pop("update_voucher_discount", True):
            order = args[0]
            try:
                discount = get_voucher_discount_for_order(order)
            except NotApplicable:
                discount = zero_money(order.currency)
            order.discount = discount
        return func(*args, **kwargs)

    return decorator


@update_voucher_discount
def recalculate_order(order: Order, **kwargs):
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
    order.discount_amount = min(order.discount_amount, total.gross.amount)
    if order.discount:
        total -= order.discount
    order.total = total
    order.save(
        update_fields=[
            "discount_amount",
            "total_net_amount",
            "total_gross_amount",
            "currency",
        ]
    )
    recalculate_order_weight(order)


def recalculate_order_weight(order):
    """Recalculate order weights."""
    weight = zero_weight()
    for line in order:
        if line.variant:
            weight += line.variant.get_weight() * line.quantity
    order.weight = weight
    order.save(update_fields=["weight"])


def update_order_prices(order, discounts):
    """Update prices in order with given discounts and proper taxes."""
    manager = get_extensions_manager()
    for line in order:  # type: OrderLine
        if line.variant:
            unit_price = line.variant.get_price(discounts)
            unit_price = TaxedMoney(unit_price, unit_price)
            line.unit_price = unit_price
            line.save(
                update_fields=[
                    "currency",
                    "unit_price_net_amount",
                    "unit_price_gross_amount",
                ]
            )

            price = manager.calculate_order_line_unit(line)
            if price != line.unit_price:
                line.unit_price = price
                if price.tax and price.net:
                    line.tax_rate = price.tax / price.net
                line.save()

    if order.shipping_method:
        order.shipping_price = manager.calculate_order_shipping(order)
        order.save(
            update_fields=[
                "shipping_price_net_amount",
                "shipping_price_gross_amount",
                "currency",
            ]
        )

    recalculate_order(order)


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
        order.save(update_fields=["status"])


def attach_order_to_user(order, user):
    """Associate existing order with user account."""
    order.user = user
    store_user_address(user, order.billing_address, AddressType.BILLING)
    if order.shipping_address:
        store_user_address(user, order.shipping_address, AddressType.SHIPPING)
    order.save(update_fields=["user"])


@transaction.atomic
def add_variant_to_order(
    order,
    variant,
    quantity,
    discounts=None,
    allow_overselling=False,
    track_inventory=True,
):
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
        line.save(update_fields=["quantity"])
    except OrderLine.DoesNotExist:
        unit_price = variant.get_price(discounts)
        unit_price = TaxedMoney(net=unit_price, gross=unit_price)
        product = variant.product
        product_name = str(product)
        variant_name = str(variant)
        translated_product_name = str(product.translated)
        translated_variant_name = str(variant.translated)
        if translated_product_name == product_name:
            translated_product_name = ""
        if translated_variant_name == variant_name:
            translated_variant_name = ""
        line = order.lines.create(
            product_name=product_name,
            variant_name=variant_name,
            translated_product_name=translated_product_name,
            translated_variant_name=translated_variant_name,
            product_sku=variant.sku,
            is_shipping_required=variant.is_shipping_required(),
            quantity=quantity,
            unit_price=unit_price,
            variant=variant,
        )
        manager = get_extensions_manager()
        unit_price = manager.calculate_order_line_unit(line)
        line.unit_price = unit_price
        line.tax_rate = unit_price.tax / unit_price.net
        line.save(
            update_fields=[
                "currency",
                "unit_price_net_amount",
                "unit_price_gross_amount",
                "tax_rate",
            ]
        )

    if variant.track_inventory and track_inventory:
        allocate_stock(variant, quantity)
    return line


def add_gift_card_to_order(order, gift_card, total_price_left):
    """Add gift card to order.

    Return a total price left after applying the gift cards.
    """
    if total_price_left > zero_money(total_price_left.currency):
        order.gift_cards.add(gift_card)
        if total_price_left < gift_card.current_balance:
            gift_card.current_balance = gift_card.current_balance - total_price_left
            total_price_left = zero_money(total_price_left.currency)
        else:
            total_price_left = total_price_left - gift_card.current_balance
            gift_card.current_balance_amount = 0
        gift_card.last_used_on = timezone.now()
        gift_card.save(update_fields=["current_balance_amount", "last_used_on"])
    return total_price_left


def change_order_line_quantity(user, line, old_quantity, new_quantity):
    """Change the quantity of ordered items in a order line."""
    if new_quantity:
        line.quantity = new_quantity
        line.save(update_fields=["quantity"])
    else:
        delete_order_line(line)

    quantity_diff = old_quantity - new_quantity

    # Create the removal event
    if quantity_diff > 0:
        events.draft_order_removed_products_event(
            order=line.order, user=user, order_lines=[(quantity_diff, line)]
        )
    elif quantity_diff < 0:
        events.draft_order_added_products_event(
            order=line.order, user=user, order_lines=[(quantity_diff * -1, line)]
        )


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
            line.save(update_fields=["quantity_fulfilled"])


def restock_fulfillment_lines(fulfillment):
    """Return fulfilled products to corresponding stocks."""
    for line in fulfillment:
        if line.order_line.variant and line.order_line.variant.track_inventory:
            increase_stock(line.order_line.variant, line.quantity, allocate=True)


def sum_order_totals(qs):
    zero = Money(0, currency=settings.DEFAULT_CURRENCY)
    taxed_zero = TaxedMoney(zero, zero)
    return sum([order.total for order in qs], taxed_zero)


def get_valid_shipping_methods_for_order(order: Order):
    return ShippingMethod.objects.applicable_shipping_methods_for_instance(
        order, price=order.get_subtotal().gross
    )
