from typing import List

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet, Value, prefetch_related_objects

from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from .models import GiftCard

GIFTCARD_FIELDS_TO_PREFETCH = [
    "used_by__first_name",
    "used_by__last_name",
    "created_by__email",
    "created_by__first_name",
    "created_by__last_name",
]
PRODUCTS_BATCH_SIZE = 100


def prepare_gift_card_search_vector_value(
    gift_card: GiftCard, *, already_prefetched=False
) -> List[NoValidationSearchVector]:
    if not already_prefetched:
        prefetch_related_objects([gift_card], *GIFTCARD_FIELDS_TO_PREFETCH)

    search_vector = [
        NoValidationSearchVector(Value(gift_card.code), config="simple"),
        NoValidationSearchVector(Value(gift_card.used_by_email), config="simple"),
        NoValidationSearchVector(Value(gift_card.created_by_email), config="simple"),
    ]
    if gift_card.used_by:
        search_vector.extend(
            [
                NoValidationSearchVector(
                    Value(gift_card.used_by.email), config="simple"
                ),
                NoValidationSearchVector(
                    Value(gift_card.used_by.first_name), config="simple"
                ),
                NoValidationSearchVector(
                    Value(gift_card.used_by.last_name), config="simple"
                ),
            ]
        )
    if gift_card.created_by:
        search_vector.extend(
            [
                NoValidationSearchVector(
                    Value(gift_card.created_by.email), config="simple"
                ),
                NoValidationSearchVector(
                    Value(gift_card.created_by.first_name), config="simple"
                ),
                NoValidationSearchVector(
                    Value(gift_card.created_by.last_name), config="simple"
                ),
            ]
        )
    return search_vector


def update_gift_card_search_vector(gift_card: GiftCard):
    gift_card.search_vector = FlatConcatSearchVector(
        *prepare_gift_card_search_vector_value(gift_card)
    )
    gift_card.save(update_fields=["search_vector", "updated_at"])


def _prep_gift_cards_search_vector_index(gift_cards: List[GiftCard]):
    prefetch_related_objects(gift_cards, *GIFTCARD_FIELDS_TO_PREFETCH)
    for gift_card in gift_cards:
        gift_card.search_vector = FlatConcatSearchVector(
            *prepare_gift_card_search_vector_value(gift_card, already_prefetched=True)
        )
        gift_card.search_index_dirty = False

    GiftCard.objects.bulk_update(
        gift_cards, ["search_vector", "updated_at", "search_index_dirty"]
    )


def update_gift_cards_search_vector(gift_cards: QuerySet):
    last_id = 0
    while True:
        gift_cards_batch = list(gift_cards.filter(id__gt=last_id)[:PRODUCTS_BATCH_SIZE])
        if not gift_cards_batch:
            break
        last_id = gift_cards_batch[-1].id
        _prep_gift_cards_search_vector_index(gift_cards_batch)


def search_gift_cards(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
