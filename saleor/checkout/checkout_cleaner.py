from typing import TYPE_CHECKING, Iterable, Optional, Type, Union

from django.core.exceptions import ValidationError

from ..discount import DiscountInfo
from ..payment import models as payment_models
from ..payment.error_codes import PaymentErrorCode
from ..plugins.manager import PluginsManager
from .error_codes import CheckoutErrorCode
from .utils import (
    call_payment_refund_or_void,
    get_active_payments,
    is_fully_covered,
    is_shipping_required,
    is_valid_shipping_method,
)

if TYPE_CHECKING:
    from .fetch import CheckoutInfo, CheckoutLineInfo


def clean_checkout_shipping(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    error_code: Union[Type[CheckoutErrorCode], Type[PaymentErrorCode]],
):
    if is_shipping_required(lines):
        if not checkout_info.shipping_method:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not set",
                        code=error_code.SHIPPING_METHOD_NOT_SET.value,
                    )
                }
            )
        if not checkout_info.shipping_address:
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        "Shipping address is not set",
                        code=error_code.SHIPPING_ADDRESS_NOT_SET.value,
                    )
                }
            )
        if not is_valid_shipping_method(checkout_info):
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not valid for your shipping address",
                        code=error_code.INVALID_SHIPPING_METHOD.value,
                    )
                }
            )


def clean_billing_address(
    checkout_info: "CheckoutInfo",
    error_code: Union[Type[CheckoutErrorCode], Type[PaymentErrorCode]],
):
    if not checkout_info.billing_address:
        raise ValidationError(
            {
                "billing_address": ValidationError(
                    "Billing address is not set",
                    code=error_code.BILLING_ADDRESS_NOT_SET.value,
                )
            }
        )


def clean_checkout_payment(
    manager: PluginsManager,
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    discounts: Iterable[DiscountInfo],
    error_code: Type[CheckoutErrorCode],
    current_payment: Optional[payment_models.Payment],
):
    clean_billing_address(checkout_info, error_code)

    if len(get_active_payments(checkout_info.checkout)) == 0:
        raise ValidationError(
            "Payment has not been initiated.",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,
        )

    if not is_fully_covered(manager, checkout_info, lines, discounts, current_payment):
        call_payment_refund_or_void(checkout_info, current_payment, manager)
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,
        )
