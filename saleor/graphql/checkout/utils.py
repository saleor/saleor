from enum import Enum
from typing import Iterable

from django.core.exceptions import ValidationError

from ...checkout.models import Checkout, CheckoutLine
from ...checkout.utils import is_fully_paid, is_valid_shipping_method
from ...discount import DiscountInfo


def clean_checkout_shipping(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    error_code: Enum,
):
    if checkout.is_shipping_required():
        if not checkout.shipping_method:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not set",
                        code=error_code.SHIPPING_METHOD_NOT_SET.value,  # type: ignore
                    )
                }
            )
        if not checkout.shipping_address:
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        "Shipping address is not set",
                        code=error_code.SHIPPING_ADDRESS_NOT_SET.value,  # type: ignore
                    )
                }
            )
        if not is_valid_shipping_method(checkout, lines, discounts):
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not valid for your shipping address",
                        code=error_code.INVALID_SHIPPING_METHOD.value,  # type: ignore
                    )
                }
            )


def clean_billing_address(checkout: Checkout, error_code: Enum):
    if not checkout.billing_address:
        raise ValidationError(
            {
                "billing_address": ValidationError(
                    "Billing address is not set",
                    code=error_code.BILLING_ADDRESS_NOT_SET.value,  # type: ignore
                )
            }
        )


def clean_checkout_payment(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    error_code: Enum,
):
    clean_billing_address(checkout, error_code)
    if not is_fully_paid(checkout, lines, discounts):
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,  # type: ignore
        )
