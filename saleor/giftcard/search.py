from typing import List

from django.contrib.postgres.search import SearchQuery
from django.db.models import Value, prefetch_related_objects

from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from .models import GiftCard

GIFTCARD_FIELDS_TO_PREFETCH = [
    "used_by__email",
    "used_by__first_name",
    "used_by__last_name",
    # "created_by__email",
    # "created_by__first_name",
    # "created_by__last_name",
]


def _add_vector(vectors: List[NoValidationSearchVector], field):
    if field:
        vectors += [NoValidationSearchVector(Value(field), config="simple")]


def prepare_gift_card_search_vector_value(
    gift_card: GiftCard,
) -> List[NoValidationSearchVector]:
    search_vectors = [NoValidationSearchVector(Value(gift_card.code), config="simple")]
    _add_vector(search_vectors, gift_card.used_by_email)
    _add_vector(search_vectors, gift_card.created_by_email)
    if gift_card.used_by:
        _add_vector(search_vectors, gift_card.used_by.email)
        _add_vector(search_vectors, gift_card.used_by.first_name)
        _add_vector(search_vectors, gift_card.used_by.last_name)
    if gift_card.created_by:
        _add_vector(search_vectors, gift_card.created_by.email)
        _add_vector(search_vectors, gift_card.created_by.first_name)
        _add_vector(search_vectors, gift_card.created_by.last_name)

    return search_vectors


def mark_gift_cards_search_index_as_dirty(gift_cards: List[GiftCard]):
    for gift_card in gift_cards:
        gift_card.search_index_dirty = True
    GiftCard.objects.bulk_update(gift_cards, ["search_index_dirty"])


def update_gift_cards_search_vector(gift_cards: List[GiftCard]):
    prefetch_related_objects(gift_cards, *GIFTCARD_FIELDS_TO_PREFETCH)
    for gift_card in gift_cards:
        gift_card.search_index_dirty = False
        gift_card.search_vector = FlatConcatSearchVector(
            *prepare_gift_card_search_vector_value(gift_card)
        )

    GiftCard.objects.bulk_update(gift_cards, ["search_vector", "search_index_dirty"])


def search_gift_cards(qs, value):
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        qs = qs.filter(search_vector=query)
    return qs
