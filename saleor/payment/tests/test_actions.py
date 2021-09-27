from decimal import Decimal
from unittest.mock import patch

import pytest

from ...plugins.manager import get_plugins_manager
from .. import PaymentError
from ..actions import try_refund


@patch("saleor.payment.actions.gateway.refund")
def test_try_refund_returns_result(
    refund_mock, order, app, payment_txn_captured, channel_PLN
):
    manager = get_plugins_manager()
    amount = Decimal("50")
    try_refund(
        order=order,
        user=None,
        app=app,
        payment=payment_txn_captured,
        manager=manager,
        channel_slug=channel_PLN.slug,
        amount=amount,
    )

    refund_mock.assert_called_once_with(
        payment_txn_captured,
        manager,
        channel_PLN.slug,
        amount,
    )


@pytest.mark.parametrize(
    "exception, message",
    [(ValueError, "Value error"), (PaymentError, "Payment error")],
)
@patch("saleor.payment.actions.events.payment_refund_failed_event")
@patch("saleor.payment.actions.gateway.refund")
def test_try_refund_catches_error(
    refund_mock,
    event_mock,
    exception,
    message,
    order,
    app,
    payment_txn_captured,
    channel_PLN,
):
    manager = get_plugins_manager()
    amount = Decimal("50")
    refund_mock.side_effect = exception(message)

    try_refund(
        order=order,
        user=None,
        app=app,
        payment=payment_txn_captured,
        manager=manager,
        channel_slug=channel_PLN.slug,
        amount=amount,
    )
    event_mock.assert_called_once_with(
        order=order, user=None, app=app, message=message, payment=payment_txn_captured
    )
