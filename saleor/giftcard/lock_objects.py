from django.db.models import QuerySet

from .models import GiftCard


def gift_card_qs_select_for_update() -> QuerySet[GiftCard]:
    return GiftCard.objects.order_by("pk").select_for_update(of=["self"])
