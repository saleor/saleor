import pytest
from prices import Money, TaxedMoney

from .....checkout.models import Checkout

CHECKOUT_COUNT_IN_BENCHMARKS = 10


@pytest.fixture
def checkouts_for_benchmarks(
    channel_USD,
    channel_PLN,
    address,
    users_for_order_benchmarks,
    variant_with_image,
    shipping_method,
):
    checkouts = [
        Checkout(
            channel=channel_USD if i % 2 else channel_PLN,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            shipping_method=shipping_method,
            user=users_for_order_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(CHECKOUT_COUNT_IN_BENCHMARKS)
    ]
    return Checkout.objects.bulk_create(checkouts)
