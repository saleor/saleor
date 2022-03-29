import random
import uuid

import pytest
from django.contrib.auth import models as auth_models
from prices import Money, TaxedMoney

from .....account import CustomerEvents
from .....account.models import CustomerEvent, User
from .....giftcard.models import GiftCard
from .....order.models import Order

ORDER_COUNT_IN_BENCHMARKS = 10
GIFT_CARDS_PER_USER = 5
EVENTS_PER_USER = 5
GROUPS_PER_USER = 5


def _prepare_events_for_user(user):
    events = [
        CustomerEvent(type=random.choice(CustomerEvents.CHOICES)[0], user=user)
        for i in range(EVENTS_PER_USER)
    ]
    return events


def _prepare_gift_cards_for_user(user):
    gift_cards = [
        GiftCard(
            created_by=user,
            initial_balance_amount=random.randint(10, 20),
            current_balance_amount=random.randint(10, 20),
            code=str(uuid.uuid4())[:16],
        )
        for i in range(GIFT_CARDS_PER_USER)
    ]
    return gift_cards


def _create_permission_groups(user):
    _groups = [
        auth_models.Group(name=str(uuid.uuid4())) for i in range(GROUPS_PER_USER)
    ]
    groups = auth_models.Group.objects.bulk_create(_groups)
    user.groups.add(*groups)
    return groups


@pytest.fixture
def users_for_customers_benchmarks(channel_USD, address, shipping_method):
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
        gift_cards.extend(_prepare_gift_cards_for_user(user))
        events.extend(_prepare_events_for_user(user))
        _create_permission_groups(user)

    CustomerEvent.objects.bulk_create(events)
    GiftCard.objects.bulk_create(gift_cards)

    return created_orders
