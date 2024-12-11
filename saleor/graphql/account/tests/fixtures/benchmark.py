import pytest
from prices import Money, TaxedMoney

from .....account.models import CustomerEvent, User
from .....giftcard.models import GiftCard
from .....order.models import Order
from .utils import (
    create_permission_groups,
    prepare_events_for_user,
    prepare_gift_cards_for_user,
)


@pytest.fixture
def users_for_customers_benchmarks(channel_USD, address, shipping_method):
    ORDER_COUNT_IN_BENCHMARKS = 10
    users = [
        User(
            email=f"jane.doe.{i}@example.com",
            is_active=True,
            default_billing_address=address.get_copy(),
            default_shipping_address=address.get_copy(),
            first_name=f"Jane_{i}",
            last_name=f"Doe_{i}",
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    users_for_customers_benchmarks = User.objects.bulk_create(users)
    for user in users_for_customers_benchmarks:
        user.addresses.add(user.default_shipping_address, user.default_billing_address)

    orders = [
        Order(
            channel=channel_USD,
            billing_address=address.get_copy(),
            shipping_address=address.get_copy(),
            shipping_method=shipping_method,
            user=users_for_customers_benchmarks[i],
            total=TaxedMoney(net=Money(i, "USD"), gross=Money(i, "USD")),
        )
        for i in range(ORDER_COUNT_IN_BENCHMARKS)
    ]
    created_orders = Order.objects.bulk_create(orders)

    events = []
    gift_cards = []

    for user in users_for_customers_benchmarks:
        gift_cards.extend(prepare_gift_cards_for_user(user))
        events.extend(prepare_events_for_user(user))
        create_permission_groups(user)

    CustomerEvent.objects.bulk_create(events)
    GiftCard.objects.bulk_create(gift_cards)

    return created_orders
