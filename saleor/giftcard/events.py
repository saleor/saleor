from typing import Optional

from ..account.models import User
from ..app.models import App
from ..core.utils.validators import user_is_valid
from . import GiftCardEvents
from .models import GiftCard, GiftCardEvent

UserType = Optional[User]
AppType = Optional[App]


def gift_card_issued_event(
    gift_card: GiftCard,
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    balance_data = {
        "currency": gift_card.currency,
        "initial_balance": gift_card.initial_balance_amount,
        "current_balance": gift_card.current_balance_amount,
    }
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.ISSUED,
        parameters={"balance": balance_data},
    )
