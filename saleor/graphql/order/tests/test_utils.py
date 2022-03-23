import pytest

from ....order import OrderStatus
from ....order.utils import invalidate_order_prices


@pytest.mark.parametrize(
    "status, invalid_prices",
    [
        (OrderStatus.DRAFT, True),
        (OrderStatus.UNCONFIRMED, True),
        (OrderStatus.UNFULFILLED, False),
    ],
)
def test_invalidate_order_prices_status(order, status, invalid_prices):
    # given
    order.invalid_prices_for_unconfirmed = False
    order.status = status

    # when
    invalidate_order_prices(order, save=False)

    # then
    assert order.invalid_prices_for_unconfirmed is invalid_prices


@pytest.mark.parametrize(
    "save, invalid_prices",
    [
        (True, True),
        (False, False),
    ],
)
def test_invalidate_order_prices_save(order, save, invalid_prices):
    # given
    order.invalid_prices_for_unconfirmed = False
    order.save(update_fields=["invalid_prices_for_unconfirmed"])
    order.status = OrderStatus.DRAFT

    # when
    invalidate_order_prices(order, save=save)

    # then
    assert order.invalid_prices_for_unconfirmed
    order.refresh_from_db()
    assert order.invalid_prices_for_unconfirmed is invalid_prices
