from unittest.mock import patch

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
