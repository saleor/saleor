from typing import TYPE_CHECKING, List

from django.db.models import Q, Value, prefetch_related_objects

from ..core.postgres import NoValidationSearchVector

if TYPE_CHECKING:
    from .models import Address, User


USER_SEARCH_FIELDS = ["email", "first_name", "last_name"]
ADDRESS_SEARCH_FIELDS = [
    "first_name",
    "last_name",
    "street_address_1",
    "street_address_2",
    "city",
    "postal_code",
    "country",
    "phone",
]


def prepare_user_search_document_value(
    user: "User", *, already_prefetched=False, attach_addresses_data=True
):
    """Prepare `search_document` user value - attach all field used in searching.

    Parameter `attach_addresses_data` should be set to False only when user
    is created and no address has been attached or user addresses are cleared.
    """
    search_document = generate_user_fields_search_document_value(user)

    if attach_addresses_data:
        if not already_prefetched:
            prefetch_related_objects(
                [user],
                "addresses",
            )
        for address in user.addresses.all():
            search_document += generate_address_search_document_value(address)

    return search_document.lower()


def generate_user_fields_search_document_value(user: "User"):
    value = "\n".join(
        [getattr(user, field) for field in USER_SEARCH_FIELDS if getattr(user, field)]
    )
    if value:
        value += "\n"
    return value.lower()


def generate_address_search_document_value(address: "Address"):
    fields_values = [
        str(getattr(address, field))
        if field != "country"
        else address.country.name + "\n" + address.country.code
        for field in ADDRESS_SEARCH_FIELDS
    ]
    return ("\n".join(fields_values) + "\n").lower()


def generate_address_search_vector_value(
    address: "Address", weight: str = "A"
) -> List[NoValidationSearchVector]:
    search_vectors = [
        NoValidationSearchVector(
            Value(address.first_name),
            Value(address.last_name),
            Value(address.street_address_1),
            Value(address.country.name),
            Value(address.country.code),
            weight=weight,
        )
    ]
    if address.company_name:
        search_vectors.append(
            NoValidationSearchVector(Value(address.company_name), weight=weight)
        )
    if address.country_area:
        search_vectors.append(
            NoValidationSearchVector(Value(address.country_area), weight=weight)
        )
    if address.city:
        search_vectors.append(
            NoValidationSearchVector(Value(address.city), weight=weight)
        )
    if address.city_area:
        search_vectors.append(
            NoValidationSearchVector(Value(address.city_area), weight=weight)
        )
    if address.street_address_2:
        search_vectors.append(
            NoValidationSearchVector(Value(address.street_address_2), weight=weight)
        )
    if address.postal_code:
        search_vectors.append(
            NoValidationSearchVector(Value(address.postal_code), weight=weight)
        )
    if address.phone:
        search_vectors.append(
            NoValidationSearchVector(Value(address.phone.as_e164), weight=weight)
        )
    return search_vectors


def search_users(qs, value):
    if value:
        lookup = Q()
        for val in value.split():
            lookup &= Q(search_document__ilike=val.lower())
        qs = qs.filter(lookup)
    return qs
