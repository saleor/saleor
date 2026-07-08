from . import events
from .models import GiftCard


def deactivate_user_gift_cards(sender, instance, **kwargs):
    """Deactivate gift cards restricted to a user that is being deleted.

    Runs on ``pre_delete`` so the ``assigned_to`` FK still points to the user
    (it is set to NULL by ``on_delete=SET_NULL`` afterwards). Once the assignee
    is gone the card can no longer be validated against its owner, so it is
    deactivated to keep it unusable.
    """
    gift_card_ids = list(
        GiftCard.objects.filter(assigned_to=instance, is_active=True).values_list(
            "id", flat=True
        )
    )
    if not gift_card_ids:
        return
    GiftCard.objects.filter(id__in=gift_card_ids).update(is_active=False)
    events.gift_cards_deactivated_event(gift_card_ids, user=None, app=None)
