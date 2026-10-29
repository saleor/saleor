from django.db.models import QuerySet

from .models import GiftCard


def gift_card_qs_select_for_update() -> QuerySet[GiftCard]:
    # order_by("pk") is intentional, not redundant: acquiring row locks in a
    # consistent primary-key order prevents deadlocks between concurrent
    # transactions that lock several rows. This mirrors every other
    # lock_objects module (see e.g. saleor/payment/lock_objects.py).
    return GiftCard.objects.order_by("pk").select_for_update(of=["self"])
