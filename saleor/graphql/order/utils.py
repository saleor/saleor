from ..core.types.common import Error


def check_for_draft_order_errors(order, errors=[]):
    # TODO: New Description
    """Return a list of errors associated with the order.

    Checks, if given order has a proper shipping address and method
    set up and return list of errors if not.
    """
    if order.get_total_quantity() == 0:
        errors.append(
            Error(
                field='lines',
                message='Could not create order without any products.'))
    if order.is_shipping_required():
        method = order.shipping_method
        shipping_address = order.shipping_address
        shipping_not_valid = (
            method and shipping_address and
            shipping_address.country.code not in method.shipping_zone.countries)  # noqa
        if shipping_not_valid:
            errors.append(
                Error(
                    field='shipping',
                    message='Shipping method is not valid for chosen shipping '
                            'address'))
    if not order.user and not order.user_email:
        errors.append(
            Error(
                field=None,
                message='Both user and user_email fields are null'))
    return errors
