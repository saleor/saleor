import graphene

from .types import GiftCard


def resolve_gift_card(info, gift_card_id):
    """Return gift card only for user assigned to it or proper staff user."""
    user = info.context.user
    gift_card = graphene.Node.get_node_from_global_id(
        info, gift_card_id, GiftCard)
    if user.has_perm('giftcard.manage_gift_card') or gift_card.creator == user:
        return gift_card
    return None
