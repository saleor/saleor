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


def gift_card_balance_reset(
    gift_card: GiftCard,
    old_gift_card: GiftCard,
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    balance_data = {
        "currency": gift_card.currency,
        "initial_balance": gift_card.initial_balance_amount,
        "current_balance": gift_card.current_balance_amount,
        "old_currency": gift_card.currency,
        "old_initial_balance": old_gift_card.initial_balance_amount,
        "old_current_balance": old_gift_card.current_balance_amount,
    }
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.BALANCE_RESET,
        parameters={"balance": balance_data},
    )


def gift_card_expiry_settings_updated(
    gift_card: GiftCard,
    old_gift_card: GiftCard,
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    expiry_data = {
        "expiry_type": gift_card.expiry_type,
        "expiry_period": gift_card.expiry_period,
        "expiry_period_type": gift_card.expiry_period_type,
        "expiry_date": gift_card.expiry_date,
        "old_expiry_type": old_gift_card.expiry_type,
        "old_expiry_period": old_gift_card.expiry_period,
        "old_expiry_period_type": old_gift_card.expiry_period_type,
        "old_expiry_date": old_gift_card.expiry_date,
    }
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.EXPIRY_SETTINGS_UPDATED,
        parameters={"expiry": expiry_data},
    )
