from collections import defaultdict

from ...giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from ..core.dataloaders import DataLoader


class GiftCardsByUserLoader(DataLoader):
    context_key = "gift_cards_by_user"

    def batch_load(self, keys):
        gift_cards = GiftCard.objects.filter(used_by_id__in=keys)
        gift_cards_by_user_map = defaultdict(list)
        for gift_card in gift_cards:
            gift_cards_by_user_map[gift_card.used_by_id].append(gift_card)
        return [gift_cards_by_user_map.get(user_id, []) for user_id in keys]


class GiftCardEventsByGiftCardIdLoader(DataLoader):
    context_key = "giftcardevents_by_giftcard"

    def batch_load(self, keys):
        events = GiftCardEvent.objects.filter(gift_card_id__in=keys)
        events_map = defaultdict(list)
        for event in events.iterator():
            events_map[event.gift_card_id].append(event)
        return [events_map.get(gift_card_id, []) for gift_card_id in keys]


class GiftCardTagsByGiftCardIdLoader(DataLoader):
    context_key = "giftcardtags_by_giftcard"

    def batch_load(self, keys):
        gift_card_gift_card_tags = GiftCard.tags.through.objects.filter(
            giftcard_id__in=keys
        )
        tags_ids = [
            gift_card_tag.giftcardtag_id for gift_card_tag in gift_card_gift_card_tags
        ]
        tags = GiftCardTag.objects.in_bulk(tags_ids)
        tags_map = defaultdict(list)
        for gift_card_tag in gift_card_gift_card_tags:
            tags_map[gift_card_tag.giftcard_id].append(
                tags[gift_card_tag.giftcardtag_id]
            )
        return [tags_map.get(gift_card_id, []) for gift_card_id in keys]
