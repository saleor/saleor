import pytest

from ...payment import ChargeStatus
from ..utils import get_active_payments, get_authorized_payments, get_captured_payments


@pytest.mark.parametrize(
    "is_active,included",
    [
        [True, True],
        [False, False],
    ],
)
def test_get_active_payments(
    is_active,
    included,
    order_with_payments,
):
    # given
    order = order_with_payments(num_payments=1)
    payment = order.payments.get()
    payment.is_active = is_active
    payment.save()
    # when
    payments = get_active_payments(order)
    # then
    assert (payment in payments) == included


@pytest.mark.parametrize(
    "charge_status,is_active,included",
    [
        [ChargeStatus.AUTHORIZED, False, False],
        [ChargeStatus.AUTHORIZED, True, True],
        [ChargeStatus.FULLY_CHARGED, True, False],
        [ChargeStatus.PARTIALLY_CHARGED, True, False],
        [ChargeStatus.NOT_CHARGED, True, False],
        [ChargeStatus.FULLY_REFUNDED, True, False],
        [ChargeStatus.PARTIALLY_CHARGED, True, False],
        [ChargeStatus.PARTIALLY_REFUNDED, True, False],
    ],
)
def test_get_authorized_payments(
    charge_status,
    is_active,
    included,
    order_with_payments,
):
    # given
    order = order_with_payments(num_payments=1)
    payment = order.payments.get()
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    # when
    payments = get_authorized_payments(order)
    # then
    assert (payment in payments) == included


@pytest.mark.parametrize(
    "charge_status,is_active,included",
    [
        [ChargeStatus.FULLY_CHARGED, False, False],
        [ChargeStatus.FULLY_CHARGED, True, True],
        [ChargeStatus.PARTIALLY_CHARGED, False, False],
        [ChargeStatus.PARTIALLY_CHARGED, True, True],
        [ChargeStatus.PARTIALLY_REFUNDED, False, False],
        [ChargeStatus.PARTIALLY_REFUNDED, True, True],
        [ChargeStatus.AUTHORIZED, True, False],
        [ChargeStatus.NOT_CHARGED, True, False],
        [ChargeStatus.FULLY_REFUNDED, True, False],
    ],
)
def test_get_captured_payments(
    charge_status,
    is_active,
    included,
    order_with_payments,
):
    # given
    order = order_with_payments(num_payments=1)
    payment = order.payments.get()
    payment.is_active = is_active
    payment.charge_status = charge_status
    payment.save()
    # when
    payments = get_captured_payments(order)
    # then
    assert (payment in payments) == included
