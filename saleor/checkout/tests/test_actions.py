import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytz
from freezegun import freeze_time

from ...tests.utils import flush_post_commit_hooks
from .. import CheckoutAuthorizeStatus, CheckoutChargeStatus
from ..actions import transaction_amounts_for_checkout_updated
from ..calculations import fetch_checkout_data
from ..fetch import fetch_checkout_info, fetch_checkout_lines


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_amounts_for_checkout_updated_fully_paid(
    mocked_fully_paid, checkout_with_items, transaction_item_generator, plugins_manager
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )

    # when
    transaction_amounts_for_checkout_updated(transaction, manager=plugins_manager)

    # then
    flush_post_commit_hooks()
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.FULL
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    mocked_fully_paid.assert_called_with(checkout)


@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
def test_transaction_amounts_for_checkout_updated_with_already_fully_paid(
    mocked_fully_paid, checkout_with_items, transaction_item_generator, plugins_manager
):
    # given
    checkout = checkout_with_items
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(checkout_info, plugins_manager, lines)
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )

    fetch_checkout_data(checkout_info, plugins_manager, lines, force_status_update=True)

    second_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )
    # when
    transaction_amounts_for_checkout_updated(
        second_transaction, manager=plugins_manager
    )

    # then
    flush_post_commit_hooks()
    checkout.refresh_from_db()
    assert checkout.charge_status == CheckoutChargeStatus.OVERCHARGED
    assert checkout.authorize_status == CheckoutAuthorizeStatus.FULL
    assert not mocked_fully_paid.called


@pytest.mark.parametrize(
    "previous_modified_at",
    [None, datetime.datetime(2018, 5, 31, 12, 0, 0, tzinfo=pytz.UTC)],
)
@patch("saleor.plugins.manager.PluginsManager.checkout_fully_paid")
@freeze_time("2023-05-31 12:00:01")
def test_transaction_amounts_for_checkout_updated_updates_last_transaction_modified_at(
    mocked_fully_paid,
    previous_modified_at,
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.last_transaction_modified_at = previous_modified_at
    checkout.save(update_fields=["last_transaction_modified_at"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=checkout_info.checkout.total.gross.amount
    )

    # when
    transaction_amounts_for_checkout_updated(transaction, manager=plugins_manager)

    # then
    flush_post_commit_hooks()
    checkout.refresh_from_db()
    assert checkout.last_transaction_modified_at == transaction.modified_at
    mocked_fully_paid.assert_called_with(checkout)


def test_get_checkout_refundable_with_transaction_and_last_refund_success(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10.0)
    )

    # when
    transaction_amounts_for_checkout_updated(transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is True


def test_get_checkout_refundable_with_transaction_and_last_refund_failure(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10.0), last_refund_success=False
    )

    # when
    transaction_amounts_for_checkout_updated(transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_transaction_without_funds(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(0)
    )

    # when
    transaction_amounts_for_checkout_updated(transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_transactions_without_funds(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(0)
    )
    transaction_item_generator(checkout_id=checkout.pk, charged_value=Decimal(0))

    # when
    transaction_amounts_for_checkout_updated(first_transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_transactions_with_failure_refund(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )

    # when
    transaction_amounts_for_checkout_updated(first_transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is False


def test_get_checkout_refundable_with_multiple_active_transactions(
    checkout_with_items,
    transaction_item_generator,
    plugins_manager,
):
    # given
    checkout = checkout_with_items
    checkout.automatically_refundable = True
    checkout.save(update_fields=["automatically_refundable"])

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    checkout_info, _ = fetch_checkout_data(
        checkout_info,
        plugins_manager,
        lines,
    )
    first_transaction = transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=False
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=True
    )
    transaction_item_generator(
        checkout_id=checkout.pk, charged_value=Decimal(10), last_refund_success=True
    )

    # when
    transaction_amounts_for_checkout_updated(first_transaction, manager=plugins_manager)

    # then
    checkout.refresh_from_db()
    assert checkout.automatically_refundable is True
