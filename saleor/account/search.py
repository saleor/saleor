from typing import TYPE_CHECKING

from django.db.models import Q

if TYPE_CHECKING:
    from .models import User


USER_SEARCH_FIELDS = ["email", "first_name", "last_name"]


def prepare_user_search_document_value(user: "User", *, attach_addresses_data=True):
    """Prepare `search_document` user value - attach all field used in searching.

    Parameter `attach_addresses_data` should be set to False only when user
    is created and no address has been attached or user addresses are cleared.
    """
    search_document = "".join([getattr(user, field) for field in USER_SEARCH_FIELDS])

    if attach_addresses_data:
        for address in user.addresses.all():
            search_document += (
                f"{address.first_name}{address.last_name}"
                f"{address.street_address_1}{address.street_address_2}"
                f"{address.city}{address.postal_code}{address.country}{address.phone}"
            )

    return search_document.replace(" ", "").lower()


def search_users(qs, value):
    if value:
        lookup = Q()
        for val in value.split():
            lookup &= Q(search_document__ilike=val.lower())
        qs = qs.filter(lookup)
    return qs
