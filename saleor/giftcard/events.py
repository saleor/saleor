from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple

from ..account.models import User
from ..app.models import App
from . import GiftCardEvents
from .models import GiftCard, GiftCardEvent

if TYPE_CHECKING:
    from ..order.models import Order


def gift_card_issued_event(
    gift_card: GiftCard,
    user: Optional[User],
    app: Optional[App],
):
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
        parameters={"balance": balance_data, "expiry_date": gift_card.expiry_date},
    )


def gift_cards_issued_event(
    gift_cards: Iterable[GiftCard],
    user: Optional[User],
    app: Optional[App],
    balance: dict,
):
    balance_data = {
        "currency": balance["currency"],
        "initial_balance": balance["amount"],
        "current_balance": balance["amount"],
    }
    events = [
        GiftCardEvent(
            gift_card=gift_card,
            user=user,
            app=app,
            type=GiftCardEvents.ISSUED,
            parameters={"balance": balance_data, "expiry_date": gift_card.expiry_date},
        )
        for gift_card in gift_cards
    ]
    return GiftCardEvent.objects.bulk_create(events)


def gift_card_sent_event(
    gift_card_id: int, user_id: Optional[int], app_id: Optional[int], email: str
):
    return GiftCardEvent.objects.create(
        gift_card_id=gift_card_id,
        user_id=user_id,
        app_id=app_id,
        type=GiftCardEvents.SENT_TO_CUSTOMER,
        parameters={"email": email},
    )


def gift_card_resent_event(
    gift_card_id: int, user_id: Optional[int], app_id: Optional[int], email: str
):
    return GiftCardEvent.objects.create(
        gift_card_id=gift_card_id,
        user_id=user_id,
        app_id=app_id,
        type=GiftCardEvents.RESENT,
        parameters={"email": email},
    )


def gift_card_balance_reset_event(
    gift_card: GiftCard,
    old_gift_card: GiftCard,
    user: Optional[User],
    app: Optional[App],
):
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


def gift_card_expiry_date_updated_event(
    gift_card: GiftCard,
    old_gift_card: GiftCard,
    user: Optional[User],
    app: Optional[App],
):
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.EXPIRY_DATE_UPDATED,
        parameters={
            "expiry_date": gift_card.expiry_date,
            "old_expiry_date": old_gift_card.expiry_date,
        },
    )


def gift_card_tags_updated_event(
    gift_card: GiftCard,
    old_tags: List[str],
    user: Optional[User],
    app: Optional[App],
):
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.TAGS_UPDATED,
        parameters={
            "tags": list(
                gift_card.tags.order_by("name").values_list("name", flat=True)
            ),
            "old_tags": old_tags,
        },
    )


def gift_card_activated_event(
    gift_card: GiftCard,
    user: Optional[User],
    app: Optional[App],
):
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.ACTIVATED,
    )


def gift_card_deactivated_event(
    gift_card: GiftCard,
    user: Optional[User],
    app: Optional[App],
):
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.DEACTIVATED,
    )


def gift_cards_activated_event(
    gift_card_ids: Iterable[int],
    user: Optional[User],
    app: Optional[App],
):
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


def gift_cards_deactivated_event(
    gift_card_ids: Iterable[int],
    user: Optional[User],
    app: Optional[App],
):
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


def gift_card_note_added_event(
    gift_card: GiftCard, user: Optional[User], app: Optional[App], message: str
) -> GiftCardEvent:
    return GiftCardEvent.objects.create(
        gift_card=gift_card,
        user=user,
        app=app,
        type=GiftCardEvents.NOTE_ADDED,
        parameters={"message": message},
    )


def gift_cards_used_in_order_event(
    balance_data: Iterable[Tuple[GiftCard, float]],
    order: "Order",
    user: Optional[User],
    app: Optional[App],
):
    events = [
        GiftCardEvent(
            gift_card=gift_card,
            user=user,
            app=app,
            order=order,
            type=GiftCardEvents.USED_IN_ORDER,
            parameters={
                "balance": {
                    "currency": gift_card.currency,
                    "current_balance": gift_card.current_balance.amount,
                    "old_current_balance": previous_balance,
                },
            },
        )
        for gift_card, previous_balance in balance_data
    ]
    return GiftCardEvent.objects.bulk_create(events)


def gift_cards_bought_event(
    gift_cards: Iterable[GiftCard],
    order: "Order",
    user: Optional[User],
    app: Optional[App],
):
    events = [
        GiftCardEvent(
            gift_card=gift_card,
            user=user,
            app=app,
            order=order,
            type=GiftCardEvents.BOUGHT,
            parameters={"expiry_date": gift_card.expiry_date},
        )
        for gift_card in gift_cards
    ]
    return GiftCardEvent.objects.bulk_create(events)
