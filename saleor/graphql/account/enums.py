import graphene
from django_countries import countries

from ...checkout import AddressType
from ...graphql.core.enums import to_enum
from ..core.utils import str_to_enum

AddressTypeEnum = to_enum(AddressType, type_name="AddressTypeEnum")


CountryCodeEnum = graphene.Enum(
    "CountryCode", [(str_to_enum(country[0]), country[0]) for country in countries]
)


class StaffMemberStatus(graphene.Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
