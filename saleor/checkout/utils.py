from django.conf import settings
from prices import Price


def get_deliveries(cart, shipping_method=None):
    """Return the cart split into shipment groups.

    Generates tuples consisting of a partition, its shipping cost and its
    total cost.

    Each partition is a list of tuples containing the cart line, its unit
    price and the line total.
    """
    for partition in cart.partition():
        if shipping_method and partition.is_shipping_required():
            shipping_cost = shipping_method.get_total()
        else:
            shipping_cost = Price(0, currency=settings.DEFAULT_CURRENCY)
        total_with_shipping = partition.get_total(
            discounts=cart.discounts) + shipping_cost

        partition = [
            (
                line,
                line.get_price_per_item(discounts=cart.discounts),
                line.get_total(discounts=cart.discounts))
            for line in partition]
        yield partition, shipping_cost, total_with_shipping


def get_subtotal(cart, shipping_method):
    """Calculate order total without shipping."""
    deliveries = get_deliveries(cart, shipping_method)
    zero = Price(0, currency=settings.DEFAULT_CURRENCY)
    cost_iterator = (
        total - shipping_cost
        for shipment, shipping_cost, total in deliveries)
    total = sum(cost_iterator, zero)
    return total


def get_total(cart, shipping_method, discount=None):
    """Calculate order total with shipping."""
    deliveries = get_deliveries(cart, shipping_method)
    zero = Price(0, currency=settings.DEFAULT_CURRENCY)
    cost_iterator = (
        total for shipment, shipping_cost, total in deliveries)
    total = sum(cost_iterator, zero)
    return total if discount is None else discount.apply(total)
