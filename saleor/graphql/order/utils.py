from django.core.exceptions import ValidationError

from ...shipping import models as shipping_models


def validate_total_quantity(order):
    if order.get_total_quantity() == 0:
        raise ValidationError({
            'lines': 'Could not create order without any products.'})


def validate_shipping_method(order):
    method = order.shipping_method
    shipping_address = order.shipping_address
    shipping_not_valid = (
        method and shipping_address and
        shipping_address.country.code not in method.shipping_zone.countries)  # noqa
    if shipping_not_valid:
        raise ValidationError({
            'shipping':
            'Shipping method is not valid for chosen shipping address'})


def validate_order_lines(order):
    for line in order:
        if line.variant is None:
            raise ValidationError({
                'lines': 'Could not create orders with non-existing products.'})


def validate_draft_order(order):
    """Checks, if given order has a proper customer data, shipping
    address and method set up and return list of errors if not.
    Checks if product variants for order lines still exists in
    database, too.
    """
    if order.is_shipping_required():
        validate_shipping_method(order)
    validate_total_quantity(order)
    validate_order_lines(order)


# FIXME: is this function needed? QS method might be enough
def applicable_shipping_methods(obj, price):
    if not obj.is_shipping_required():
        return []
    if not obj.shipping_address:
        return []

    qs = shipping_models.ShippingMethod.objects
    return qs.applicable_shipping_methods(
        price=price, weight=obj.get_total_weight(),
        country_code=obj.shipping_address.country.code)
