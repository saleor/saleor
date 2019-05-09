from ...shipping import models as shipping_models
from ..core.types.common import Error


def _check_can_finalize_products_quantity(order, errors):
    if order.get_total_quantity() == 0:
        errors.append(
            Error(field="lines", message="Could not create order without any products.")
        )


def _check_can_finalize_shipping(order, errors):
    if order.is_shipping_required():
        method = order.shipping_method
        shipping_address = order.shipping_address
        shipping_not_valid = (
            method
            and shipping_address
            and shipping_address.country.code not in method.shipping_zone.countries
        )  # noqa
        if shipping_not_valid:
            errors.append(
                Error(
                    field="shipping",
                    message="Shipping method is not valid for chosen shipping "
                    "address",
                )
            )


def _check_can_finalize_products_exists(order, errors):
    line_variants = [line.variant for line in order]
    if None in line_variants:
        errors.append(
            Error(
                field="lines",
                message="Could not create orders with non-existing products.",
            )
        )


def can_finalize_draft_order(order, errors):
    """Return a list of errors associated with the order.

    Checks, if given order has a proper customer data, shipping
    address and method set up and return list of errors if not.
    Checks if product variants for order lines still exists in
    database, too.
    """
    _check_can_finalize_products_quantity(order, errors)
    _check_can_finalize_shipping(order, errors)
    _check_can_finalize_products_exists(order, errors)
    return errors


def applicable_shipping_methods(obj, info, price):
    if not obj.is_shipping_required():
        return []
    if not obj.shipping_address:
        return []

    qs = shipping_models.ShippingMethod.objects
    return qs.applicable_shipping_methods(
        price=price,
        weight=obj.get_total_weight(),
        country_code=obj.shipping_address.country.code,
    )
