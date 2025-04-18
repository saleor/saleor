import pytest

from ... import OrderStatus
from ...calculations import fetch_order_prices_if_expired


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_order_prices(
    order_with_lines,
    plugins_manager,
    django_assert_num_queries,
    tax_configuration_flat_rates,
    count_queries,
):
    # given
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED

    # when & then
    with django_assert_num_queries(28):
        fetch_order_prices_if_expired(order, plugins_manager, None, True)
