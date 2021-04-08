import random
import uuid

import pytest
from prices import Money, TaxedMoney

from .....account.models import User
from .....order.models import Order
from .....payment import ChargeStatus
from .....payment.models import Payment

ORDER_COUNT_IN_BENCHMARKS = 10
PAYMENTS_PER_ORDER = 1


def _create_payments_for_order(order):
    return [
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=random.choice(ChargeStatus.CHOICES)[0],
        )
        for _ in range(PAYMENTS_PER_ORDER)
    ]


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
def orders_for_benchmarks(channel_USD, address, payment_dummy, users_for_benchmarks):
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
    payments = []
    for order in created_orders:
        payment = _create_payments_for_order(order)
        payments.extend(payment)
    Payment.objects.bulk_create(payments)
    return created_orders
