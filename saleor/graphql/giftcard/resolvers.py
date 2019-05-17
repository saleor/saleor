import graphene

from ...giftcard import models
from ...graphql.core.utils import from_global_id_strict_type
from ..core.utils import get_node_optimized
from .types import GiftCard


def resolve_gift_card(info, gift_card_global_id):
    """Return gift card only for user assigned to it or proper staff user."""
    user = info.context.user
    if user.has_perm("giftcard.manage_gift_card"):
        return graphene.Node.get_node_from_global_id(
            info, gift_card_global_id, GiftCard
        )
    gift_card_id = from_global_id_strict_type(info, gift_card_global_id, GiftCard)
    return get_node_optimized(
        models.GiftCard.objects, {"pk": gift_card_id, "buyer": user}, info
    )
