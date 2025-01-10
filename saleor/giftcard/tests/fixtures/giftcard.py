import datetime
import secrets

import pytest

from ....core.prices import Money
from ....graphql.giftcard.tests.benchmark import GIFT_CARD_COUNT_IN_BENCHMARKS
from ... import GiftCardEvents
from ...models import GiftCard, GiftCardEvent, GiftCardTag


@pytest.fixture
def gift_card(customer_user):
    gift_card = GiftCard.objects.create(
        code="never_expiry",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )
    tag, _ = GiftCardTag.objects.get_or_create(name="test-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_with_metadata(customer_user):
    return GiftCard.objects.create(
        code="card_with_meta",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
        metadata={"test": "value"},
    )


@pytest.fixture
def gift_card_expiry_date(customer_user):
    gift_card = GiftCard.objects.create(
        code="expiry_date",
        created_by=customer_user,
        created_by_email=customer_user.email,
        initial_balance=Money(20, "USD"),
        current_balance=Money(20, "USD"),
        expiry_date=datetime.datetime.now(tz=datetime.UTC).date()
        + datetime.timedelta(days=100),
    )
    tag = GiftCardTag.objects.create(name="another-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_used(staff_user, customer_user):
    gift_card = GiftCard.objects.create(
        code="giftcard_used",
        created_by=staff_user,
        used_by=customer_user,
        created_by_email=staff_user.email,
        used_by_email=customer_user.email,
        initial_balance=Money(100, "USD"),
        current_balance=Money(80, "USD"),
    )
    tag = GiftCardTag.objects.create(name="tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_created_by_staff(staff_user):
    gift_card = GiftCard.objects.create(
        code="created_by_staff",
        created_by=staff_user,
        created_by_email=staff_user.email,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )
    tag, _ = GiftCardTag.objects.get_or_create(name="test-tag")
    gift_card.tags.add(tag)
    return gift_card


@pytest.fixture
def gift_card_list():
    gift_cards = list(
        GiftCard.objects.bulk_create(
            [
                GiftCard(
                    code="code-test-1",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
                GiftCard(
                    code="code-test-2",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
                GiftCard(
                    code="code-test-3",
                    initial_balance=Money(10, "USD"),
                    current_balance=Money(10, "USD"),
                ),
            ]
        )
    )
    return gift_cards


@pytest.fixture
def gift_cards_for_benchmarks(
    staff_user,
    gift_card,
    customer_user,
):
    gift_cards = [
        GiftCard(
            code=secrets.token_hex(8),
            created_by=customer_user,
            created_by_email=customer_user.email,
            initial_balance=Money(10, "USD"),
            current_balance=Money(10, "USD"),
        )
        for _ in range(GIFT_CARD_COUNT_IN_BENCHMARKS)
    ]
    created_gift_cards = GiftCard.objects.bulk_create(gift_cards)
    tag = GiftCardTag.objects.create(name="benchmark-test-tag")
    tag.gift_cards.add(*created_gift_cards)

    parameters = {
        "message": "test message",
        "email": "testemail@email.com",
    }
    events = []
    for gift_card in gift_cards:
        events.append(
            GiftCardEvent(
                user=staff_user,
                gift_card=gift_card,
                type=GiftCardEvents.ISSUED,
                parameters=parameters,
            )
        )

    GiftCardEvent.objects.bulk_create(events)

    return created_gift_cards
