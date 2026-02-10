from django.conf import settings
from django.db.models import Q, QuerySet, Value, prefetch_related_objects

from ..account.models import User
from ..core.db.connection import allow_writer
from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector
from .models import GiftCard

GIFTCARD_FIELDS_TO_PREFETCH = ["used_by", "created_by"]


def _add_vector(vectors: list[NoValidationSearchVector], field, weight: str):
    if field:
        vectors += [
            NoValidationSearchVector(Value(field), config="simple", weight=weight)
        ]


def prepare_gift_card_search_vector_value(
    gift_card: GiftCard,
) -> list[NoValidationSearchVector]:
    search_vectors = [
        NoValidationSearchVector(
            Value(gift_card.code[-4:]), config="simple", weight="A"
        ),
        NoValidationSearchVector(Value(gift_card.code), config="simple", weight="B"),
    ]
    for tag in gift_card.tags.all()[: settings.GIFT_CARD_MAX_INDEXED_TAGS]:
        _add_vector(search_vectors, tag.name, weight="B")
    _add_vector(search_vectors, gift_card.used_by_email, weight="C")
    _add_vector(search_vectors, gift_card.created_by_email, weight="C")
    if gift_card.used_by:
        _add_vector(search_vectors, gift_card.used_by.email, weight="C")
        _add_vector(search_vectors, gift_card.used_by.first_name, weight="C")
        _add_vector(search_vectors, gift_card.used_by.last_name, weight="C")
    if gift_card.created_by:
        _add_vector(search_vectors, gift_card.created_by.email, weight="C")
        _add_vector(search_vectors, gift_card.created_by.first_name, weight="C")
        _add_vector(search_vectors, gift_card.created_by.last_name, weight="C")
    return search_vectors


def mark_gift_cards_search_index_as_dirty(gift_cards: list[GiftCard] | QuerySet):
    for gift_card in gift_cards:
        gift_card.search_index_dirty = True
    GiftCard.objects.bulk_update(gift_cards, ["search_index_dirty"])


def mark_gift_cards_search_index_as_dirty_by_users(users: list[User]):
    emails = [user.email for user in users]
    gift_cards = GiftCard.objects.filter(
        Q(used_by_email__in=emails)
        | Q(created_by_email__in=emails)
        | Q(used_by__in=users)
        | Q(created_by__in=users)
    )
    mark_gift_cards_search_index_as_dirty(gift_cards)


@allow_writer()
def update_gift_cards_search_vector(gift_cards: list[GiftCard]):
    prefetch_related_objects(gift_cards, *GIFTCARD_FIELDS_TO_PREFETCH)
    for gift_card in gift_cards:
        gift_card.search_index_dirty = False
        gift_card.search_vector = FlatConcatSearchVector(
            *prepare_gift_card_search_vector_value(gift_card)
        )

    GiftCard.objects.bulk_update(gift_cards, ["search_vector", "search_index_dirty"])
