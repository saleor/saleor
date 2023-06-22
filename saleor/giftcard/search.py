from typing import List

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, Value, prefetch_related_objects

from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from .models import GiftCard

GIFTCARD_FIELDS_TO_PREFETCH = [
    "used_by__first_name",
    "used_by__last_name",
    "created_by__email",
    "created_by__first_name",
    "created_by__last_name",
]


def prepare_gift_card_search_vector_value(
    gift_card: GiftCard,
) -> List[NoValidationSearchVector]:
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


def mark_gift_card_search_index_as_dirty(gift_card: GiftCard):
    gift_card.search_index_dirty = True
    gift_card.save(update_fields=["search_index_dirty", "updated_at"])


def update_gift_cards_search_vector(gift_cards: List[GiftCard]):
    prefetch_related_objects(gift_cards, *GIFTCARD_FIELDS_TO_PREFETCH)
    for gift_card in gift_cards:
        gift_card.search_vector = FlatConcatSearchVector(
            *prepare_gift_card_search_vector_value(gift_card)
        )
        gift_card.search_index_dirty = False

    GiftCard.objects.bulk_update(
        gift_cards, ["search_vector", "updated_at", "search_index_dirty"]
    )


def search_gift_cards(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
