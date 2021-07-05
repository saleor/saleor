from collections import defaultdict

from ...giftcard.models import GiftCard
from ..core.dataloaders import DataLoader


class GiftCardsByUserLoader(DataLoader):
    context_key = "gift_cards_by_user"

    def batch_load(self, keys):
        gift_cards = GiftCard.objects.filter(user_id__in=keys)
        gift_cards_by_user_map = defaultdict(list)
        for gift_card in gift_cards:
            gift_cards_by_user_map[gift_card.user_id].append(gift_card)
        return [gift_cards_by_user_map.get(user_id, []) for user_id in keys]
