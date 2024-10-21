import random
import uuid

from .....account import CustomerEvents
from .....account.models import CustomerEvent, Group
from .....giftcard.models import GiftCard

GIFT_CARDS_PER_USER = 5
EVENTS_PER_USER = 5
GROUPS_PER_USER = 5


def prepare_events_for_user(user):
    events = [
        CustomerEvent(type=random.choice(CustomerEvents.CHOICES)[0], user=user)
        for _ in range(EVENTS_PER_USER)
    ]
    return events


def prepare_gift_cards_for_user(user):
    gift_cards = [
        GiftCard(
            created_by=user,
            initial_balance_amount=random.randint(10, 20),
            current_balance_amount=random.randint(10, 20),
            code=str(uuid.uuid4())[:16],
        )
        for _ in range(GIFT_CARDS_PER_USER)
    ]
    return gift_cards


def create_permission_groups(user):
    _groups = [Group(name=str(uuid.uuid4())) for i in range(GROUPS_PER_USER)]
    groups = Group.objects.bulk_create(_groups)
    user.groups.add(*groups)
    return groups
