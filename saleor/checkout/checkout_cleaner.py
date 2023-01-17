from datetime import date
from typing import TYPE_CHECKING, Iterable, List, Optional, Type, Union

import graphene
from django.core.exceptions import ValidationError

from ..core.exceptions import GiftCardNotApplicable
from ..core.taxes import TaxError
from ..discount import DiscountInfo
from ..giftcard.models import GiftCard
from ..payment import gateway
from ..payment import models as payment_models
from ..payment.error_codes import PaymentErrorCode
from ..plugins.manager import PluginsManager
from . import models
from .error_codes import CheckoutErrorCode, OrderCreateFromCheckoutErrorCode
from .models import Checkout
from .utils import clear_delivery_method, is_fully_paid, is_shipping_required

if TYPE_CHECKING:
    from .fetch import CheckoutInfo, CheckoutLineInfo


def clean_checkout_shipping(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    error_code: Union[
        Type[CheckoutErrorCode],
        Type[PaymentErrorCode],
        Type[OrderCreateFromCheckoutErrorCode],
    ],
):
    delivery_method_info = checkout_info.delivery_method_info

    if is_shipping_required(lines):
        if not delivery_method_info.delivery_method:
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Shipping method is not set",
                        code=error_code.SHIPPING_METHOD_NOT_SET.value,
                    )
                }
            )
        if not delivery_method_info.is_valid_delivery_method():
            raise ValidationError(
                {
                    "shipping_address": ValidationError(
                        "Shipping address is not set",
                        code=error_code.SHIPPING_ADDRESS_NOT_SET.value,
                    )
                }
            )
        if not delivery_method_info.is_method_in_valid_methods(checkout_info):
            clear_delivery_method(checkout_info)
            raise ValidationError(
                {
                    "shipping_method": ValidationError(
                        "Delivery method is not valid for your shipping address",
                        code=error_code.INVALID_SHIPPING_METHOD.value,
                    )
                }
            )


def clean_billing_address(
    checkout_info: "CheckoutInfo",
    error_code: Union[
        Type[CheckoutErrorCode],
        Type[PaymentErrorCode],
        Type[OrderCreateFromCheckoutErrorCode],
    ],
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
    last_payment: Optional[payment_models.Payment],
):
    clean_billing_address(checkout_info, error_code)
    if not is_fully_paid(manager, checkout_info, lines, discounts):
        gateway.payment_refund_or_void(
            last_payment, manager, channel_slug=checkout_info.channel.slug
        )
        raise ValidationError(
            "Provided payment methods can not cover the checkout's total amount",
            code=error_code.CHECKOUT_NOT_FULLY_PAID.value,
        )


def validate_checkout_email(checkout: models.Checkout):
    if not checkout.email:
        raise ValidationError(
            "Checkout email must be set.",
            code=CheckoutErrorCode.EMAIL_NOT_SET.value,
        )


def _validate_gift_cards(checkout: Checkout):
    """Check if all gift cards assigned to checkout are available."""
    today = date.today()
    all_gift_cards = GiftCard.objects.filter(checkouts=checkout.token).count()
    active_gift_cards = (
        GiftCard.objects.active(date=today).filter(checkouts=checkout.token).count()
    )
    if not all_gift_cards == active_gift_cards:
        msg = "Gift card has expired. Order placement cancelled."
        raise GiftCardNotApplicable(msg)


def validate_checkout(
    checkout_info: "CheckoutInfo",
    lines: Iterable["CheckoutLineInfo"],
    unavailable_variant_pks: Iterable[int],
    discounts: List["DiscountInfo"],
    manager: "PluginsManager",
):
    """Validate all required data for converting checkout into order."""
    if not checkout_info.channel.is_active:
        raise ValidationError(
            {
                "channel": ValidationError(
                    "Cannot complete checkout with inactive channel.",
                    code=OrderCreateFromCheckoutErrorCode.CHANNEL_INACTIVE.value,
                )
            }
        )
    if unavailable_variant_pks:
        not_available_variants_ids = {
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in unavailable_variant_pks
        }
        code = OrderCreateFromCheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Some of the checkout lines variants are unavailable.",
                    code=code,
                    params={"variants": not_available_variants_ids},
                )
            }
        )
    if not lines:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot complete checkout without lines",
                    code=OrderCreateFromCheckoutErrorCode.NO_LINES.value,
                )
            }
        )

    if checkout_info.checkout.voucher_code and not checkout_info.voucher:
        raise ValidationError(
            {
                "voucher_code": ValidationError(
                    "Voucher not applicable",
                    code=OrderCreateFromCheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
                )
            }
        )
    validate_checkout_email(checkout_info.checkout)

    clean_billing_address(checkout_info, OrderCreateFromCheckoutErrorCode)
    clean_checkout_shipping(checkout_info, lines, OrderCreateFromCheckoutErrorCode)
    _validate_gift_cards(checkout_info.checkout)

    # call plugin's hooks to validate if we are able to create an order
    # can raise TaxError
    try:
        manager.preprocess_order_creation(checkout_info, discounts, lines)
    except TaxError as tax_error:
        raise ValidationError(
            f"Unable to calculate taxes - {str(tax_error)}",
            code=OrderCreateFromCheckoutErrorCode.TAX_ERROR.value,
        )
