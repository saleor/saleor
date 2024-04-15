"""Checkout-related utility functions."""

from collections.abc import Iterable
from typing import Optional

from django.conf import settings
from django.db.models import Exists, Q
from prices import Money

from ..core.db.connection import allow_writer
from ..core.taxes import zero_money
from ..payment.models import TransactionItem
from . import CheckoutAuthorizeStatus, CheckoutChargeStatus
from .models import Checkout


def _update_charge_status(
    checkout: Checkout,
    checkout_total_gross: Money,
    total_charged: Money,
    checkout_has_lines: bool,
):
    zero_money_amount = zero_money(checkout.currency)
    total_charged = max(zero_money_amount, total_charged)
    checkout_with_only_zero_price_lines = (
        checkout_has_lines and checkout_total_gross <= zero_money_amount
    )

    if total_charged <= zero_money_amount and checkout_with_only_zero_price_lines:
        checkout.charge_status = CheckoutChargeStatus.FULL
    elif total_charged <= zero_money_amount:
        checkout.charge_status = CheckoutChargeStatus.NONE
    elif total_charged < checkout_total_gross:
        checkout.charge_status = CheckoutChargeStatus.PARTIAL
    elif total_charged == checkout_total_gross:
        checkout.charge_status = CheckoutChargeStatus.FULL
    elif total_charged > checkout_total_gross:
        checkout.charge_status = CheckoutChargeStatus.OVERCHARGED
    else:
        checkout.charge_status = CheckoutChargeStatus.NONE


def _update_authorize_status(
    checkout: Checkout,
    checkout_total_gross: Money,
    total_authorized: Money,
    total_charged: Money,
    checkout_has_lines: bool,
):
    total_covered = total_authorized + total_charged
    zero_money_amount = zero_money(checkout.currency)

    checkout_with_only_zero_price_lines = (
        checkout_has_lines and checkout_total_gross <= zero_money_amount
    )

    if total_covered <= zero_money_amount and checkout_with_only_zero_price_lines:
        checkout.authorize_status = CheckoutAuthorizeStatus.FULL
    elif total_covered == zero_money_amount:
        checkout.authorize_status = CheckoutAuthorizeStatus.NONE
    elif total_covered >= checkout_total_gross:
        checkout.authorize_status = CheckoutAuthorizeStatus.FULL
    elif total_covered < checkout_total_gross and total_covered > zero_money_amount:
        checkout.authorize_status = CheckoutAuthorizeStatus.PARTIAL
    else:
        checkout.authorize_status = CheckoutAuthorizeStatus.NONE


def _get_payment_amount_for_checkout(
    checkout_transactions: Iterable["TransactionItem"], currency: str
) -> tuple[Money, Money]:
    total_charged_amount = zero_money(currency)
    total_authorized_amount = zero_money(currency)
    for transaction in checkout_transactions:
        total_authorized_amount += transaction.amount_authorized
        total_authorized_amount += transaction.amount_authorize_pending

        total_charged_amount += transaction.amount_charged
        total_charged_amount += transaction.amount_charge_pending
    return total_authorized_amount, total_charged_amount


def update_checkout_payment_statuses(
    checkout: Checkout,
    checkout_total_gross: Money,
    checkout_has_lines: bool,
    checkout_transactions: Optional[Iterable["TransactionItem"]] = None,
    save: bool = True,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    current_authorize_status = checkout.authorize_status
    current_charge_status = checkout.charge_status

    if checkout_transactions is None:
        checkout_transactions = checkout.payment_transactions.all().using(
            database_connection_name
        )
    total_authorized_amount, total_charged_amount = _get_payment_amount_for_checkout(
        checkout_transactions, checkout.currency
    )
    _update_authorize_status(
        checkout,
        checkout_total_gross,
        total_authorized_amount,
        total_charged_amount,
        checkout_has_lines,
    )
    _update_charge_status(
        checkout, checkout_total_gross, total_charged_amount, checkout_has_lines
    )
    if save:
        fields_to_update = []
        if current_authorize_status != checkout.authorize_status:
            fields_to_update.append("authorize_status")
        if current_charge_status != checkout.charge_status:
            fields_to_update.append("charge_status")
        if fields_to_update:
            fields_to_update.append("last_change")
            with allow_writer():
                checkout.save(update_fields=fields_to_update)


def update_refundable_for_checkout(checkout_pk):
    """Update automatically refundable status for checkout.

    The refundable status is calculated based on the transaction. If transaction is
    not refundable or doesn't have enough funds to refund, the function will calculate
    the status based on the rest of transactions for the checkout.
    """
    transactions_subquery = TransactionItem.objects.filter(
        Q(checkout_id=checkout_pk, last_refund_success=True)
        & (Q(authorized_value__gt=0) | Q(charged_value__gt=0))
    )
    Checkout.objects.filter(pk=checkout_pk).update(
        automatically_refundable=Exists(transactions_subquery)
    )
