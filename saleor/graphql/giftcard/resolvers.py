from django.conf import settings

from ...giftcard import models


def resolve_gift_card(id):
    return (
        models.GiftCard.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(pk=id)
        .first()
    )


def resolve_gift_cards():
    return models.GiftCard.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).all()


def resolve_gift_card_tags():
    return models.GiftCardTag.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).all()
