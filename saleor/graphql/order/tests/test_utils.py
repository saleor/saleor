from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from pytz import utc

from ....order import OrderStatus
from ..mutations.utils import invalidate_order_prices

NOW = datetime(year=2000, month=1, day=1).replace(tzinfo=utc)


@freeze_time(NOW)
@pytest.mark.parametrize(
    "status, updated_fields, price_expiration",
    [
        (OrderStatus.DRAFT, ["price_expiration_for_unconfirmed"], NOW),
        (OrderStatus.UNCONFIRMED, ["price_expiration_for_unconfirmed"], NOW),
        (OrderStatus.UNFULFILLED, [], NOW + timedelta(minutes=30)),
    ],
)
def test_invalidate_order_prices_status(
    order, status, updated_fields, price_expiration
):
    # given
    order.price_expiration_for_unconfirmed = NOW + timedelta(minutes=30)
    order.status = status

    # when
    invalidate_fields = invalidate_order_prices(order, save=False)

    # then
    assert invalidate_fields == updated_fields
    assert order.price_expiration_for_unconfirmed == price_expiration


@freeze_time(NOW)
@pytest.mark.parametrize(
    "save, updated_fields, price_expiration_from_db",
    [
        (True, [], NOW),
        (False, ["price_expiration_for_unconfirmed"], NOW + timedelta(minutes=30)),
    ],
)
def test_invalidate_order_prices_save(
    order, save, updated_fields, price_expiration_from_db
):
    # given
    order.price_expiration_for_unconfirmed = NOW + timedelta(minutes=30)
    order.save(update_fields=["price_expiration_for_unconfirmed"])
    order.status = OrderStatus.DRAFT

    # when
    invalidate_fields = invalidate_order_prices(order, save=save)

    # then
    assert order.price_expiration_for_unconfirmed == NOW
    assert invalidate_fields == updated_fields
    order.refresh_from_db()
    assert order.price_expiration_for_unconfirmed == price_expiration_from_db
