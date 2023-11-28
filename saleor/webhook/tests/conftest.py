from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mocked_fetch_checkout():
    def mocked_fetch_side_effect(
        checkout_info, manager, lines, address, force_update=False
    ):
        return checkout_info, lines

    with patch(
        "saleor.checkout.calculations.fetch_checkout_data",
        new=Mock(side_effect=mocked_fetch_side_effect),
    ) as mocked_fetch:
        yield mocked_fetch


@pytest.fixture
def mocked_fetch_order():
    def mocked_fetch_side_effect(order, manager, lines, force_update=False):
        return order, lines

    with patch(
        "saleor.order.calculations.fetch_order_prices_if_expired",
        new=Mock(side_effect=mocked_fetch_side_effect),
    ) as mocked_fetch:
        yield mocked_fetch
