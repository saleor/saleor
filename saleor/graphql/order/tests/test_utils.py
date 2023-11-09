import pytest

from ....order import OrderStatus
from ....order.utils import invalidate_order_prices


@pytest.mark.parametrize(
    ("status", "invalid_prices"),
    [
        (OrderStatus.DRAFT, True),
        (OrderStatus.UNCONFIRMED, True),
        (OrderStatus.UNFULFILLED, False),
    ],
)
def test_invalidate_order_prices_status(order, status, invalid_prices):
    # given
    order.should_refresh_prices = False
    order.status = status

    # when
    invalidate_order_prices(order, save=False)

    # then
    assert order.should_refresh_prices is invalid_prices


@pytest.mark.parametrize(
    ("save", "invalid_prices"),
    [
        (True, True),
        (False, False),
    ],
)
def test_invalidate_order_prices_save(order, save, invalid_prices):
    # given
    order.should_refresh_prices = False
    order.save(update_fields=["should_refresh_prices"])
    order.status = OrderStatus.DRAFT

    # when
    invalidate_order_prices(order, save=save)

    # then
    assert order.should_refresh_prices
    order.refresh_from_db()
    assert order.should_refresh_prices is invalid_prices
