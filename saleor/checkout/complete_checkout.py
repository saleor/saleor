from typing import List, Optional, Tuple

from django.core.exceptions import ValidationError
from django.db import transaction

from ..account.error_codes import AccountErrorCode
from ..account.models import User
from ..core.exceptions import InsufficientStock
from ..core.taxes import TaxError
from ..core.utils.url import validate_storefront_url
from ..discount import DiscountInfo
from ..discount.models import NotApplicable
from ..graphql.checkout.utils import (  # TODO move from graphql
    clean_checkout_payment,
    clean_checkout_shipping,
)
from ..order import models as order_models
from ..order.models import Order
from ..payment import PaymentError, gateway
from ..payment.models import Payment, Transaction
from ..payment.utils import store_customer_id
from . import models
from .calculations import calculate_checkout_total_with_gift_cards
from .error_codes import CheckoutErrorCode
from .utils import abort_order_data, create_order, get_order, prepare_order_data


@transaction.atomic
def prepare_checkout(checkout: models.Checkout, discounts, tracking_code, redirect_url):
    lines = list(checkout)

    clean_checkout_shipping(checkout, lines, discounts, CheckoutErrorCode)
    clean_checkout_payment(checkout, lines, discounts, CheckoutErrorCode)

    payment = checkout.get_last_active_payment()

    validate_payment_amount(discounts, payment, checkout)

    if redirect_url:
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )

    to_update = []
    if redirect_url and redirect_url != checkout.redirect_url:
        checkout.redirect_url = redirect_url
        to_update.append("redirect_url")

    if tracking_code and tracking_code != checkout.tracking_code:
        checkout.tracking_code = tracking_code
        to_update.append("tracking_code")

    if to_update:
        checkout.save(update_fields=to_update)


@transaction.atomic
def convert_checkout_to_order(
    checkout: models.Checkout, order_data: dict, user: Optional[User]
) -> order_models.Order:
    order = create_order(
        checkout=checkout, order_data=order_data, user=user,  # type: ignore
    )
    # remove checkout after order is successfully created
    checkout.delete()
    return order


def validate_payment_amount(discounts, payment, checkout):
    if (
        payment.total
        != calculate_checkout_total_with_gift_cards(checkout, discounts).gross.amount
    ):
        gateway.payment_refund_or_void(payment)
        raise ValidationError(
            "Payment does not cover all checkout value.",
            code=CheckoutErrorCode.CHECKOUT_NOT_FULLY_PAID.value,
        )


def get_order_data(checkout: models.Checkout, discounts: List[DiscountInfo]) -> dict:
    try:
        with transaction.atomic():
            order_data = prepare_order_data(
                checkout=checkout, lines=list(checkout), discounts=discounts,
            )
    except InsufficientStock as e:
        raise ValidationError(f"Insufficient product stock: {e.item}", code=e.code)
    except NotApplicable:
        raise ValidationError(
            "Voucher not applicable",
            code=CheckoutErrorCode.VOUCHER_NOT_APPLICABLE.value,
        )
    except TaxError as tax_error:
        raise ValidationError(
            "Unable to calculate taxes - %s" % str(tax_error),
            code=CheckoutErrorCode.TAX_ERROR.value,
        )
    return order_data


def process_payment(
    payment: Payment,
    store_source: bool,
    payment_data: Optional[dict],
    order_data: dict,
) -> Transaction:
    try:
        if payment.to_confirm:
            txn = gateway.confirm(payment, additional_data=payment_data)
        else:
            txn = gateway.process_payment(
                payment=payment,
                token=payment.token,
                store_source=store_source,
                additional_data=payment_data,
            )
        payment.refresh_from_db()
        if not txn.is_success:
            raise PaymentError(txn.error)
    except PaymentError as e:
        abort_order_data(order_data)
        raise ValidationError(str(e), code=CheckoutErrorCode.PAYMENT_ERROR.value)
    return txn


def complete_checkout(
    checkout: models.Checkout,
    payment_data,
    store_source,
    discounts,
    user,
    tracking_code=None,
    redirect_url=None,
) -> Tuple[Optional[Order], bool, dict]:
    action_required = False
    action_data = {}  # type: ignore
    order = get_order(checkout.token)
    if order:
        return order, action_required, action_data
    prepare_checkout(
        checkout=checkout,
        discounts=discounts,
        tracking_code=tracking_code,
        redirect_url=redirect_url,
    )

    payment = checkout.get_last_active_payment()
    try:
        order_data = get_order_data(checkout, discounts)
    except ValidationError as error:
        gateway.payment_refund_or_void(payment)
        raise error

    txn = process_payment(
        payment=payment,  # type: ignore
        store_source=store_source,
        payment_data=payment_data,
        order_data=order_data,
    )

    if txn.customer_id and user.is_authenticated:
        store_customer_id(user, payment.gateway, txn.customer_id)  # type: ignore

    action_required = txn.action_required
    action_data = txn.action_required_data if action_data else {}

    if not action_required:
        try:
            with transaction.atomic():
                order = get_order(checkout.token)
                if order:
                    # Order was created asynchronously, we can release the lock made
                    # on order_data
                    abort_order_data(order_data)
                else:
                    order = convert_checkout_to_order(
                        checkout=checkout, order_data=order_data, user=user
                    )
        except InsufficientStock as e:
            abort_order_data(order_data)
            gateway.payment_refund_or_void(payment)
            raise ValidationError(f"Insufficient product stock: {e.item}", code=e.code)

    if not order:
        abort_order_data(order_data)

    return order, action_required, action_data
