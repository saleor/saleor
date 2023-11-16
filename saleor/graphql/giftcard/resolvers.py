from ...giftcard import models
from ..core.context import get_database_connection_name


def resolve_gift_card(info, id):
    return (
        models.GiftCard.objects.using(get_database_connection_name(info.context))
        .filter(pk=id)
        .first()
    )


def resolve_gift_cards(info):
    return models.GiftCard.objects.using(
        get_database_connection_name(info.context)
    ).all()


def resolve_gift_card_tags(info):
    return models.GiftCardTag.objects.using(
        get_database_connection_name(info.context)
    ).all()
