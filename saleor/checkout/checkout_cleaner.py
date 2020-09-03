from typing import Iterable, Optional, Type, Union

from django.core.exceptions import ValidationError

from ..discount import DiscountInfo
from ..payment import gateway, models as payment_models
from ..payment.error_codes import PaymentErrorCode
from .error_codes import CheckoutErrorCode
from .models import Checkout, CheckoutLine
from .utils import is_fully_paid, is_valid_shipping_method


def clean_checkout_shipping(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    error_code: Union[Type[CheckoutErrorCode], Type[PaymentErrorCode]],
):
    if checkout.is_shipping_required():
        if not checkout.shipping_method:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not set",
                        code=error_code.SHIPPING_METHOD_NOT_SET.value,
                    )
                }
            )
        if not checkout.shipping_address:
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        "Shipping address is not set",
                        code=error_code.SHIPPING_ADDRESS_NOT_SET.value,
                    )
                }
            )
        if not is_valid_shipping_method(checkout, lines, discounts):
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not valid for your shipping address",
                        code=error_code.INVALID_SHIPPING_METHOD.value,
                    )
                }
            )


def clean_billing_address(
    checkout: Checkout,
    error_code: Union[Type[CheckoutErrorCode], Type[PaymentErrorCode]],
):
    if not checkout.billing_address:
        raise ValidationError(
            {
                "billing_address": ValidationError(
                    "Billing address is not set",
                    code=error_code.BILLING_ADDRESS_NOT_SET.value,
                )
            }
        )


def clean_checkout_payment(
    checkout: Checkout,
    lines: Iterable[CheckoutLine],
    discounts: Iterable[DiscountInfo],
    error_code: Type[CheckoutErrorCode],
    last_payment: Optional[payment_models.Payment],
):
    clean_billing_address(checkout, error_code)
    if not is_fully_paid(checkout, lines, discounts):
        gateway.payment_refund_or_void(last_payment)
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,
        )
