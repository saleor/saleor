from django.core.exceptions import ValidationError

from ...order.error_codes import OrderErrorCode


def validate_total_quantity(order):
    if order.get_total_quantity() == 0:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Could not create order without any products.",
                    code=OrderErrorCode.REQUIRED,
                )
            }
        )


def validate_shipping_method(order):
    method = order.shipping_method
    shipping_address = order.shipping_address
    shipping_not_valid = (
        method
        and shipping_address
        and shipping_address.country.code not in method.shipping_zone.countries
    )  # noqa
    if shipping_not_valid:
        raise ValidationError(
            {
                "shipping": ValidationError(
                    "Shipping method is not valid for chosen shipping address",
                    code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE,
                )
            }
        )


def validate_order_lines(order):
    for line in order:
        if line.variant is None:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Could not create orders with non-existing products.",
                        code=OrderErrorCode.NOT_FOUND,
                    )
                }
            )


def validate_draft_order(order):
    """Check if the given order contains the proper data.

    - Has proper customer data,
    - Shipping address and method are set up,
    - Product variants for order lines still exists in database.

    Returns a list of errors if any were found.
    """
    if order.is_shipping_required():
        validate_shipping_method(order)
    validate_total_quantity(order)
    validate_order_lines(order)
