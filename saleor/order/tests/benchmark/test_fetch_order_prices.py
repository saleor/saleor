import pytest

from ....discount.models import OrderDiscount, OrderLineDiscount
from ....tax import TaxCalculationStrategy
from ... import OrderStatus
from ...calculations import fetch_order_prices_if_expired


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_order_prices_catalogue_discount(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
    django_assert_num_queries,
    count_queries,
):
    # given
    OrderLineDiscount.objects.all().delete()
    order = order_with_lines_and_catalogue_promotion
    channel = order.channel

    tc = channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # when
    with django_assert_num_queries(38):
        fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
