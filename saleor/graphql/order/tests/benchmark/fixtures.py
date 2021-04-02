import uuid

import pytest
from prices import Money, TaxedMoney

from .....order.models import Order


@pytest.fixture
def orders_for_benchmarks(channel_USD, address, customer_user):
    orders = [
        Order(
            token=str(uuid.uuid4()),
            channel=channel_USD,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            user=customer_user,
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(10)
    ]
    return Order.objects.bulk_create(orders)
