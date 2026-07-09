import pytest
from django.db.models import ProtectedError

from ..models import GiftCard


def test_gift_card_can_be_assigned_to_customer(gift_card, customer_user):
    # when
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # then
    gift_card.refresh_from_db()
    assert gift_card.assigned_to == customer_user
    assert gift_card.assigned_to_email == customer_user.email
    assert gift_card in GiftCard.objects.filter(assigned_to=customer_user)
    assert customer_user.assigned_gift_cards.filter(pk=gift_card.pk).exists()


def test_deleting_assigned_customer_is_protected(gift_card, customer_user):
    # given a card restricted to the customer
    gift_card.assigned_to = customer_user
    gift_card.assigned_to_email = customer_user.email
    gift_card.save(update_fields=["assigned_to", "assigned_to_email"])

    # when / then: assigned_to is on_delete=PROTECT, so a raw delete is refused.
    # Deletion must go through deactivate_assigned_gift_cards() first (used by
    # the user-deletion mutations).
    with pytest.raises(ProtectedError):
        customer_user.delete()
