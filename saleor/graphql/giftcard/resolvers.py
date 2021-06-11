from ...giftcard import models


def resolve_gift_card(gift_card_id):
    return models.GiftCard.objects.filter(pk=gift_card_id).first()


def resolve_gift_cards():
    return models.GiftCard.objects.all()
