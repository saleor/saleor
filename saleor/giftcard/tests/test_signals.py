from .. import GiftCardEvents
from ..models import GiftCardEvent


def test_deleting_user_deactivates_assigned_gift_cards(gift_card, customer_user):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.is_active = True
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])

    # when
    customer_user.delete()

    # then
    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    # assigned_to is nulled by on_delete=SET_NULL after the card is deactivated.
    assert gift_card.assigned_to_id is None
    assert GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.DEACTIVATED
    ).exists()


def test_deleting_user_keeps_gift_cards_assigned_to_others_active(
    gift_card, customer_user, staff_user
):
    # given
    gift_card.assigned_to = staff_user
    gift_card.assigned_to_email = staff_user.email
    gift_card.is_active = True
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])

    # when
    customer_user.delete()

    # then
    gift_card.refresh_from_db()
    assert gift_card.is_active is True
    assert gift_card.assigned_to == staff_user
    assert not GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.DEACTIVATED
    ).exists()


def test_deleting_user_ignores_already_inactive_gift_cards(gift_card, customer_user):
    # given
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.is_active = False
    gift_card.save(update_fields=["assigned_to", "assigned_to_email", "is_active"])

    # when
    customer_user.delete()

    # then
    gift_card.refresh_from_db()
    assert gift_card.is_active is False
    assert not GiftCardEvent.objects.filter(
        gift_card=gift_card, type=GiftCardEvents.DEACTIVATED
    ).exists()
