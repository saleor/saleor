import random
from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from .....account.models import User
from .....order import OrderEvents, OrderStatus
from .....order.models import Fulfillment, FulfillmentLine, Order, OrderEvent, OrderLine
from .....payment import ChargeStatus
from .....payment.models import Payment, Transaction

ORDER_COUNT_IN_BENCHMARKS = 10
EVENTS_PER_ORDER = 5
LINES_PER_ORDER = 3
TRANSACTIONS_PER_PAYMENT = 3


def _prepare_payment_transactions(payments):
    transactions = []

    for payment in payments:
        transactions.extend(
            [
                Transaction(payment=payment, gateway_response=str(index))
                for index in range(TRANSACTIONS_PER_PAYMENT)
            ]
        )

    return transactions


def _prepare_payments_for_order(order):
    return [
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.NOT_CHARGED,
        ),
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.PARTIALLY_CHARGED,
            captured_amount=Decimal("6.0"),
        ),
        Payment(
            gateway="mirumee.payments.dummy",
            order=order,
            is_active=True,
            charge_status=ChargeStatus.FULLY_CHARGED,
            captured_amount=Decimal("10.0"),
        ),
    ]


def _prepare_events_for_order(order):
    return [
        OrderEvent(order=order, type=random.choice(OrderEvents.CHOICES)[0])
        for _ in range(EVENTS_PER_ORDER)
    ]


def _prepare_lines_for_order(order, variant_with_image):
    price = TaxedMoney(
        net=Money(amount=5, currency="USD"),
        gross=Money(amount=5, currency="USD"),
    )
    return [
        OrderLine(
            order=order,
            variant=variant_with_image,
            quantity=5,
            is_shipping_required=True,
            is_gift_card=False,
            unit_price=price,
            total_price=price,
        )
        for _ in range(LINES_PER_ORDER)
    ]


@pytest.fixture
def users_for_order_benchmarks(address):
    users = [
        User(
            email=f"john.doe.{i}@example.com",
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
def orders_for_benchmarks(
    channel_USD,
    channel_PLN,
    address,
    payment_dummy,
    users_for_order_benchmarks,
    variant_with_image,
    shipping_method,
    stocks_for_cc,
):
    orders = [
        Order(
            channel=channel_USD if i % 2 else channel_PLN,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            shipping_method=shipping_method,
            user=users_for_order_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    created_orders = Order.objects.bulk_create(orders)

    payments = []
    events = []
    fulfillments = []
    fulfillment_lines = []
    lines = []
    transactions = []

    for index, order in enumerate(created_orders):
        new_payments = _prepare_payments_for_order(order)
        new_transactions = _prepare_payment_transactions(new_payments)
        new_events = _prepare_events_for_order(order)
        new_lines = _prepare_lines_for_order(order, variant_with_image)
        payments.extend(new_payments)
        transactions.extend(new_transactions)
        events.extend(new_events)
        lines.extend(new_lines)
        fulfillment = Fulfillment(order=order, fulfillment_order=order.number)
        fulfillments.append(fulfillment)

        fulfillment_lines.append(
            FulfillmentLine(
                order_line=new_lines[0],
                fulfillment=fulfillment,
                stock=stocks_for_cc[index % 3] if index % 2 else None,
                quantity=index,
            )
        )

    Payment.objects.bulk_create(payments)
    Transaction.objects.bulk_create(transactions)
    OrderEvent.objects.bulk_create(events)
    Fulfillment.objects.bulk_create(fulfillments)
    OrderLine.objects.bulk_create(lines)
    FulfillmentLine.objects.bulk_create(fulfillment_lines)

    return created_orders


@pytest.fixture
def draft_orders_for_benchmarks(orders_for_benchmarks):
    for order in orders_for_benchmarks:
        order.status = OrderStatus.DRAFT

    Order.objects.bulk_update(orders_for_benchmarks, ["status"])

    return orders_for_benchmarks
