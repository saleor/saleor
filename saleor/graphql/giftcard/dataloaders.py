from collections import defaultdict

from ...checkout.models import Checkout
from ...giftcard.models import GiftCard, GiftCardEvent, GiftCardTag
from ...order.models import Order
from ..core.dataloaders import DataLoader


class GiftCardsByUserLoader(DataLoader):
    context_key = "gift_cards_by_user"

    def batch_load(self, keys):
        gift_cards = GiftCard.objects.using(self.database_connection_name).filter(
            used_by_id__in=keys
        )
        gift_cards_by_user_map = defaultdict(list)
        for gift_card in gift_cards:
            gift_cards_by_user_map[gift_card.used_by_id].append(gift_card)
        return [gift_cards_by_user_map.get(user_id, []) for user_id in keys]


class GiftCardEventsByGiftCardIdLoader(DataLoader):
    context_key = "giftcardevents_by_giftcard"

    def batch_load(self, keys):
        events = GiftCardEvent.objects.using(self.database_connection_name).filter(
            gift_card_id__in=keys
        )
        events_map = defaultdict(list)
        for event in events.iterator():
            events_map[event.gift_card_id].append(event)
        return [events_map.get(gift_card_id, []) for gift_card_id in keys]


class GiftCardTagsByGiftCardIdLoader(DataLoader):
    context_key = "giftcardtags_by_giftcard"

    def batch_load(self, keys):
        # there is no typing information available for through models
        # so we resolve to getattr, which is safer than ignoring everything
        gift_card_gift_card_tags = GiftCard.tags.through.objects.using(
            self.database_connection_name
        ).filter(giftcard_id__in=keys)
        tags_ids = [
            getattr(gift_card_tag, "giftcardtag_id")
            for gift_card_tag in gift_card_gift_card_tags
        ]
        tags = GiftCardTag.objects.using(self.database_connection_name).in_bulk(
            tags_ids
        )
        tags_map = defaultdict(list)
        for gift_card_tag in gift_card_gift_card_tags:
            tags_map[getattr(gift_card_tag, "giftcard_id")].append(
                tags[getattr(gift_card_tag, "giftcardtag_id")]
            )
        return [tags_map.get(gift_card_id, []) for gift_card_id in keys]


class GiftCardsByOrderIdLoader(DataLoader):
    context_key = "gift_cards_by_order_id"

    def batch_load(self, keys):
        # there is no typing information available for through models
        # so we resolve to getattr, which is safer than ignoring everything
        gift_card_orders = Order.gift_cards.through.objects.using(
            self.database_connection_name
        ).filter(order_id__in=keys)
        gift_cards = GiftCard.objects.using(self.database_connection_name).in_bulk(
            [getattr(order, "giftcard_id") for order in gift_card_orders]
        )
        cards_map = defaultdict(list)
        for gift_card_order in gift_card_orders:
            cards_map[getattr(gift_card_order, "order_id")].append(
                gift_cards[getattr(gift_card_order, "giftcard_id")]
            )
        return [cards_map.get(order_id, []) for order_id in keys]


class GiftCardsByCheckoutIdLoader(DataLoader):
    context_key = "gift_cards_by_checkout_id"

    def batch_load(self, keys):
        checkouts_and_gift_cards_pairs = (
            Checkout.gift_cards.through.objects.using(self.database_connection_name)
            .filter(checkout_id__in=keys)
            .values_list("checkout_id", "giftcard_id")
        )

        gift_cards = GiftCard.objects.using(self.database_connection_name).in_bulk(
            [gift_card_id for _, gift_card_id in checkouts_and_gift_cards_pairs]
        )

        cards_map = defaultdict(list)
        for checkout_id, gift_card_id in checkouts_and_gift_cards_pairs:
            cards_map[checkout_id].append(gift_cards[gift_card_id])

        return [cards_map.get(checkout_id, []) for checkout_id in keys]
