import graphene
from django_countries import countries

from ...account import CustomerEvents
from ...checkout import AddressType
from ...graphql.core.enums import to_enum
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.utils import str_to_enum
from ..directives import doc

AddressTypeEnum = to_enum(AddressType, type_name="AddressTypeEnum")

CustomerEventsEnum = doc(DOC_CATEGORY_USERS, to_enum(CustomerEvents))


CountryCodeEnum = graphene.Enum(
    "CountryCode",
    [(str_to_enum(country[0]), country[0]) for country in countries],
    description=(
        "Represents country codes defined by the ISO 3166-1 alpha-2 standard."
        "\n\nThe `EU` value is DEPRECATED and will be removed in Saleor 3.21."
    ),
)


@doc(category=DOC_CATEGORY_USERS)
class StaffMemberStatus(graphene.Enum):
    """Represents the status of a staff account."""

    ACTIVE = "active"
    DEACTIVATED = "deactivated"

    @property
    def description(self):
        if self == StaffMemberStatus.ACTIVE:
            return "User account has been activated."
        if self == StaffMemberStatus.DEACTIVATED:
            return "User account has not been activated yet."
        return None
