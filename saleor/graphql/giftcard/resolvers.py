import graphene

from ...giftcard import models
from .types import GiftCard


def resolve_gift_card(info, gift_card_global_id):
    return graphene.Node.get_node_from_global_id(info, gift_card_global_id, GiftCard)


def resolve_gift_cards():
    return models.GiftCard.objects.all()
