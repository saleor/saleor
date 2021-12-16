from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from pytz import utc

from ....order import OrderStatus
from ..mutations.utils import invalidate_order_prices

TEST_DATE = datetime(year=2000, month=1, day=1).replace(tzinfo=utc)


@freeze_time(TEST_DATE)
@pytest.mark.parametrize(
    "status, updated_fields, price_expiration",
    [
        (OrderStatus.DRAFT, ["price_expiration_for_unconfirmed"], TEST_DATE),
        (OrderStatus.UNCONFIRMED, ["price_expiration_for_unconfirmed"], TEST_DATE),
        (OrderStatus.UNFULFILLED, [], TEST_DATE + timedelta(minutes=30)),
    ],
)
def test_invalidate_order_prices_status(
    order, status, updated_fields, price_expiration
):
    # given
    order.price_expiration_for_unconfirmed = TEST_DATE + timedelta(minutes=30)
    order.status = status

    # when
    invalidate_fields = invalidate_order_prices(order, save=False)

    # then
    assert invalidate_fields == updated_fields
    assert order.price_expiration_for_unconfirmed == price_expiration


@freeze_time(TEST_DATE)
@pytest.mark.parametrize(
    "save, updated_fields, price_expiration_from_db",
    [
        (True, [], TEST_DATE),
        (
            False,
            ["price_expiration_for_unconfirmed"],
            TEST_DATE + timedelta(minutes=30),
        ),
    ],
)
def test_invalidate_order_prices_save(
    order, save, updated_fields, price_expiration_from_db
):
    # given
    order.price_expiration_for_unconfirmed = TEST_DATE + timedelta(minutes=30)
    order.save(update_fields=["price_expiration_for_unconfirmed"])
    order.status = OrderStatus.DRAFT

    # when
    invalidate_fields = invalidate_order_prices(order, save=save)

    # then
    assert order.price_expiration_for_unconfirmed == TEST_DATE
    assert invalidate_fields == updated_fields
    order.refresh_from_db()
    assert order.price_expiration_for_unconfirmed == price_expiration_from_db
