import random
import uuid

import pytest
from prices import Money, TaxedMoney

from .....account.models import User
from .....order import OrderEvents
from .....order.models import Order, OrderEvent

ORDER_COUNT_IN_BENCHMARKS = 10
EVENTS_PER_ORDER = 5


@pytest.fixture
def users_for_benchmarks(address):
    users = [
        User(
            email=f"john.doe.{i}@exmaple.com",
            is_active=True,
            default_billing_address=address.get_copy(),
            default_shipping_address=address.get_copy(),
            first_name=f"John_{i}",
            last_name=f"Doe_{i}",
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    return User.objects.bulk_create(users)


@pytest.fixture
def orders_for_benchmarks(channel_USD, address, users_for_benchmarks):
    orders = [
        Order(
            token=str(uuid.uuid4()),
            channel=channel_USD,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            user=users_for_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    created_orders = Order.objects.bulk_create(orders)

    events = [
        OrderEvent(order=order, type=random.choice(OrderEvents.CHOICES)[0])
        for order in created_orders
    ]
    OrderEvent.objects.bulk_create(events)
    return created_orders
