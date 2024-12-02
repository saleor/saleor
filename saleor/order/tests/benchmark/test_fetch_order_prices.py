import pytest

from ....discount.models import OrderLineDiscount
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
    OrderLineDiscount.objects.all().delete()
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED

    # when & then
    with django_assert_num_queries(39):
        fetch_order_prices_if_expired(order, plugins_manager, None, True)
