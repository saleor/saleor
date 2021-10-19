from unittest import mock
from unittest.mock import ANY

from ..tasks import refund_or_void_inactive_payment


@mock.patch("saleor.payment.tasks.task_logger.info")
@mock.patch("saleor.payment.tasks.gateway.payment_refund_or_void")
def test_refund_or_void_inactive_payment_for_completed_order(
    payment_refund_or_void,
    logger_info,
    payment_txn_preauth,
):
    # given
    payment = payment_txn_preauth
    # when
    refund_or_void_inactive_payment(payment_txn_preauth.pk)
    # then
    payment_refund_or_void.assert_called_once_with(payment, ANY, ANY)
    assert logger_info.call_count == 1


@mock.patch("saleor.payment.tasks.task_logger.error")
@mock.patch("saleor.payment.tasks.gateway.payment_refund_or_void")
def test_refund_or_void_inactive_payment_for_payment_without_channel(
    payment_refund_or_void,
    logger_error,
    payment_txn_preauth,
):
    # given
    payment = payment_txn_preauth
    payment.order = None
    payment.save()
    # when
    refund_or_void_inactive_payment(payment_txn_preauth.pk)
    # then
    assert payment_refund_or_void.call_count == 0
    assert logger_error.call_count == 1
