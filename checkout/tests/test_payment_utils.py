from decimal import Decimal

import pytest

from .. import CheckoutChargeStatus
from ..payment_utils import update_checkout_payment_statuses


@pytest.mark.parametrize(
    ("checkout_total", "charged_value", "has_lines", "expected_charge_status"),
    [
        (Decimal(-1), Decimal(-1), False, CheckoutChargeStatus.NONE),
        (Decimal(0), Decimal(-1), False, CheckoutChargeStatus.NONE),
        (Decimal(0), Decimal(0), True, CheckoutChargeStatus.FULL),
        (Decimal(0), Decimal(0), False, CheckoutChargeStatus.NONE),
        (Decimal(1), Decimal(0), False, CheckoutChargeStatus.NONE),
        (Decimal(1), Decimal(0.5), False, CheckoutChargeStatus.PARTIAL),
        (Decimal(1), Decimal(1), False, CheckoutChargeStatus.FULL),
        (Decimal(0), Decimal(1), False, CheckoutChargeStatus.OVERCHARGED),
        (Decimal(1), Decimal(2), False, CheckoutChargeStatus.OVERCHARGED),
        (Decimal(1), Decimal(0), True, CheckoutChargeStatus.NONE),
        (Decimal(1), Decimal(0.5), True, CheckoutChargeStatus.PARTIAL),
        (Decimal(1), Decimal(1), True, CheckoutChargeStatus.FULL),
        (Decimal(0), Decimal(1), True, CheckoutChargeStatus.OVERCHARGED),
        (Decimal(1), Decimal(2), True, CheckoutChargeStatus.OVERCHARGED),
    ],
)
def test_checkout_charge_status(
    checkout_total,
    charged_value,
    has_lines,
    expected_charge_status,
    checkout_with_prices,
    transaction_item_generator,
):
    # given
    checkout_with_prices.total_gross_amount = checkout_total
    checkout_with_prices.total_net_amount = checkout_total

    tr = transaction_item_generator(
        checkout_id=checkout_with_prices.pk, charged_value=charged_value
    )

    # when
    update_checkout_payment_statuses(
        checkout_with_prices,
        checkout_total_gross=checkout_with_prices.total.gross,
        checkout_has_lines=has_lines,
        checkout_transactions=[tr],
    )

    # then
    checkout_with_prices.refresh_from_db()
    assert checkout_with_prices.charge_status == expected_charge_status
