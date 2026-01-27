from typing import TYPE_CHECKING

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet, Value, prefetch_related_objects

from ..core.postgres import FlatConcatSearchVector, NoValidationSearchVector

if TYPE_CHECKING:
    from .models import Address, User

USER_SEARCH_FIELDS = [
    "email",
    "first_name",
    "last_name",
]


def update_user_search_vector(
    user: "User", *, attach_addresses_data: bool = True, save: bool = True
) -> None:
    """Update the user's search vector for full-text search.

    Args:
        user: The user instance to update.
        attach_addresses_data: If True, includes address data in the search vector.
            Set to False when creating a user without addresses or clearing addresses.
        save: If True, saves the user instance to the database immediately.

    """
    user.search_vector = FlatConcatSearchVector(
        *generate_user_search_vector_value(
            user, attach_addresses_data=attach_addresses_data
        )
    )
    if save:
        user.save(update_fields=["search_vector", "updated_at"])


def generate_user_search_vector_value(
    user: "User",
    *,
    attach_addresses_data: bool = True,
    already_prefetched: bool = False,
) -> list[NoValidationSearchVector]:
    search_vectors = [
        NoValidationSearchVector(
            Value(user.email),
            Value(user.first_name),
            Value(user.last_name),
            config="simple",
            weight="A",
        ),
    ]
    if attach_addresses_data:
        if not already_prefetched:
            prefetch_related_objects(
                [user],
                "addresses",
            )
        for address in user.addresses.all():
            search_vectors.extend(
                generate_address_search_vector_value(address, weight="B")
            )
    return search_vectors


def generate_address_search_vector_value(
    address: "Address", weight: str = "A"
) -> list[NoValidationSearchVector]:
    search_vectors = [
        NoValidationSearchVector(
            Value(address.first_name),
            Value(address.last_name),
            Value(address.street_address_1),
            Value(address.country.name),
            Value(address.country.code),
            config="simple",
            weight=weight,
        ),
    ]
    if address.company_name:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.company_name), config="simple", weight=weight
            )
        )
    if address.country_area:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.country_area), config="simple", weight=weight
            )
        )
    if address.city:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.city), config="simple", weight=weight
            )
        )
    if address.city_area:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.city_area), config="simple", weight=weight
            )
        )
    if address.street_address_2:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.street_address_2), config="simple", weight=weight
            )
        )
    if address.postal_code:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.postal_code), config="simple", weight=weight
            )
        )
    if address.phone:
        search_vectors.append(
            NoValidationSearchVector(
                Value(address.phone.as_e164), config="simple", weight=weight
            )
        )
    return search_vectors


def search_users(qs: "QuerySet[User]", value) -> "QuerySet[User]":
    if value:
        query = SearchQuery(value, search_type="websearch", config="simple")
        lookup = Q(search_vector=query)
        qs = qs.filter(lookup).annotate(
            search_rank=SearchRank(F("search_vector"), query)
        )
    return qs
