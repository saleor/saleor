from typing import Iterable, Optional

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


def gift_card_sent(
    gift_card_id: int, user_id: Optional[int], app_id: Optional[int], email: str
):
    return GiftCardEvent.objects.create(
        gift_card_id=gift_card_id,
        user_id=user_id,
        app_id=app_id,
        type=GiftCardEvents.SENT_TO_CUSTOMER,
        parameters={"email": email},
    )


def gift_card_resent(
    gift_card_id: int, user_id: Optional[int], app_id: Optional[int], email: str
):
    return GiftCardEvent.objects.create(
        gift_card_id=gift_card_id,
        user_id=user_id,
        app_id=app_id,
        type=GiftCardEvents.RESENT,
        parameters={"email": email},
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


def gift_card_activated(
    gift_card: GiftCard,
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.ACTIVATED,
    )


def gift_card_deactivated(
    gift_card: GiftCard,
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.DEACTIVATED,
    )


def gift_cards_activated(
    gift_card_ids: Iterable[int],
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    events = [
        GiftCardEvent(
            gift_card_id=gift_card_id,
            user=user,
            app=app,
            type=GiftCardEvents.ACTIVATED,
        )
        for gift_card_id in gift_card_ids
    ]
    return GiftCardEvent.objects.bulk_create(events)


def gift_cards_deactivated(
    gift_card_ids: Iterable[int],
    user: UserType,
    app: AppType,
):
    if not user_is_valid(user):
        user = None
    events = [
        GiftCardEvent(
            gift_card_id=gift_card_id,
            user=user,
            app=app,
            type=GiftCardEvents.DEACTIVATED,
        )
        for gift_card_id in gift_card_ids
    ]
    return GiftCardEvent.objects.bulk_create(events)


def gift_card_note_added(
    gift_card: GiftCard, user: UserType, app: AppType, message: str
) -> GiftCardEvent:
    if not user_is_valid(user):
        user = None
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.NOTE_ADDED,
        parameters={"message": message},
    )
