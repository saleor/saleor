from typing import TYPE_CHECKING, Iterable, Optional, Type, Union

from django.core.exceptions import ValidationError

from ..discount import DiscountInfo
from ..payment import gateway
from ..payment import models as payment_models
from ..payment.error_codes import PaymentErrorCode
from ..plugins.manager import PluginsManager
from . import CheckoutLineInfo
from .error_codes import CheckoutErrorCode
from .models import Checkout
from .utils import is_fully_paid, is_shipping_required, is_valid_shipping_method

if TYPE_CHECKING:
    from prices import TaxedMoney


def clean_checkout_shipping(
    checkout: Checkout,
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable[DiscountInfo],
    error_code: Union[Type[CheckoutErrorCode], Type[PaymentErrorCode]],
    subtotal: Optional["TaxedMoney"] = None,
):
    if is_shipping_required(lines):
        if not checkout.shipping_method_id:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not set",
                        code=error_code.SHIPPING_METHOD_NOT_SET.value,
                    )
                }
            )
        if not checkout.shipping_address_id:
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        "Shipping address is not set",
                        code=error_code.SHIPPING_ADDRESS_NOT_SET.value,
                    )
                }
            )
        if not is_valid_shipping_method(checkout, lines, discounts, subtotal):
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
    if not checkout.billing_address_id:
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
    checkout: Checkout,
    lines: Iterable[CheckoutLineInfo],
    discounts: Iterable[DiscountInfo],
    error_code: Type[CheckoutErrorCode],
    last_payment: Optional[payment_models.Payment],
):
    clean_billing_address(checkout, error_code)
    if not is_fully_paid(manager, checkout, lines, discounts):
        gateway.payment_refund_or_void(last_payment)
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,
        )
