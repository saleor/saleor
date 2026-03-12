import pytest
from prices import Money, TaxedMoney

from ....checkout.models import Checkout

CHECKOUT_COUNT_IN_BENCHMARKS = 10


@pytest.fixture
def checkouts_for_benchmarks(
    channel_USD,
    channel_PLN,
    address,
    users_for_order_benchmarks,
    variant_with_image,
    checkout_delivery,
    shipping_zones_with_different_channels,
):
    shipping_method = shipping_zones_with_different_channels[0].shipping_methods.first()
    checkouts = [
        Checkout(
            channel=channel_USD if i % 2 else channel_PLN,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            user=users_for_order_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(CHECKOUT_COUNT_IN_BENCHMARKS)
    ]
    checkouts = Checkout.objects.bulk_create(checkouts)
    for checkout in checkouts:
        checkout.assigned_delivery = checkout_delivery(checkout, shipping_method)
    Checkout.objects.bulk_update(
        checkouts,
        ["assigned_delivery_id"],
    )
    return checkouts
